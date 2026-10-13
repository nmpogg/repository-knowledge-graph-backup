"""Conversation rows, revision, and delete guards. Turn policy lives in T-018."""

from __future__ import annotations

import uuid
from typing import Any

import kuzu

from rkg.storage._util import fetch_all, fetch_one, loads_json, ts_param
from rkg.storage.conversation_json import encode_state
from rkg.storage.errors import (
    ConversationBusyError,
    ConversationConflictError,
    NotFoundError,
)
from rkg.storage.records import ConversationRecord, Page
from rkg.storage.snapshots import get_snapshot

# Structured focus/pending. Focus stays isolated per conversation row.
DEFAULT_CONVERSATION_STATE: dict[str, Any] = {
    "focus_entity_id": None,
    "pending_candidate_ids": [],
    "state_version": 2,
    "pending_intent": None,
}

_CONV_RETURN = (
    "c.id, c.repository_id, c.snapshot_id, c.title, c.revision, "
    "c.state_json, c.created_at, c.updated_at"
)


def _row_to_conversation(row: list[Any]) -> ConversationRecord:
    (
        conv_id,
        repository_id,
        snapshot_id,
        title,
        revision,
        state_json,
        created_at,
        updated_at,
    ) = row
    return ConversationRecord(
        id=conv_id,
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        title=title,
        revision=int(revision),
        state=loads_json(state_json, default=None),
        created_at=created_at,
        updated_at=updated_at,
    )


def create_conversation(
    conn: kuzu.Connection,
    *,
    repository_id: str,
    snapshot_id: str,
    title: str = "",
    state: dict[str, Any] | None = None,
    conversation_id: str | None = None,
) -> ConversationRecord:
    # Ownership + snapshot existence; derives repository from snapshot contract.
    get_snapshot(conn, repository_id, snapshot_id)
    cid = conversation_id or f"conv_{uuid.uuid4().hex}"
    now = ts_param()
    stored_state = DEFAULT_CONVERSATION_STATE if state is None else state
    conn.execute(
        "CREATE (c:Conversation {"
        "id: $id, repository_id: $rid, snapshot_id: $sid, title: $title, "
        "revision: 1, state_json: $state, created_at: timestamp($ts), "
        "updated_at: timestamp($ts)})",
        {
            "id": cid,
            "rid": repository_id,
            "sid": snapshot_id,
            "title": title,
            "state": encode_state(stored_state),
            "ts": now,
        },
    )
    return get_conversation(conn, cid)


def list_conversations(
    conn: kuzu.Connection,
    *,
    repository_id: str | None = None,
    snapshot_id: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> Page:
    """Newest first. Filters are optional and independent."""
    if offset < 0 or limit < 1:
        raise ValueError("offset/limit out of range")
    limit = min(limit, 100)
    clauses: list[str] = []
    filters: dict[str, Any] = {}
    if repository_id:
        clauses.append("c.repository_id = $rid")
        filters["rid"] = repository_id
    if snapshot_id:
        clauses.append("c.snapshot_id = $sid")
        filters["sid"] = snapshot_id
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total_row = fetch_one(
        conn, f"MATCH (c:Conversation){where} RETURN count(c)", filters
    )
    items = fetch_all(
        conn,
        f"MATCH (c:Conversation){where} RETURN {_CONV_RETURN} "
        "ORDER BY c.updated_at DESC, c.id ASC SKIP $o LIMIT $l",
        {**filters, "o": offset, "l": limit},
    )
    return Page(
        items=tuple(_row_to_conversation(row) for row in items),
        offset=offset,
        limit=limit,
        total=int(total_row[0]) if total_row else 0,
    )


def get_conversation(
    conn: kuzu.Connection, conversation_id: str
) -> ConversationRecord:
    row = fetch_one(
        conn,
        f"MATCH (c:Conversation {{id: $id}}) RETURN {_CONV_RETURN}",
        {"id": conversation_id},
    )
    if row is None:
        raise NotFoundError("conversation not found")
    return _row_to_conversation(row)


def count_pending_turns(conn: kuzu.Connection, conversation_id: str) -> int:
    row = fetch_one(
        conn,
        "MATCH (t:Turn {conversation_id: $id, status: 'pending'}) RETURN count(t)",
        {"id": conversation_id},
    )
    return int(row[0]) if row else 0


def advance_revision(
    conn: kuzu.Connection, conversation_id: str, expected_revision: int
) -> ConversationRecord:
    """Optimistic +1. Snapshot pin and focus are left unchanged."""
    updated = fetch_one(
        conn,
        f"MATCH (c:Conversation {{id: $id}}) WHERE c.revision = $expected "
        f"SET c.revision = $expected + 1, c.updated_at = timestamp($ts) "
        f"RETURN {_CONV_RETURN}",
        {"id": conversation_id, "expected": expected_revision, "ts": ts_param()},
    )
    if updated is None:
        raise ConversationConflictError("conversation revision conflict")
    return _row_to_conversation(updated)


def write_state(
    conn: kuzu.Connection,
    conversation_id: str,
    *,
    expected_revision: int,
    state: dict[str, Any],
) -> ConversationRecord:
    """Replace structured state only when the revision still matches.

    Does not change ``snapshot_id`` or revision.
    """
    updated = fetch_one(
        conn,
        f"MATCH (c:Conversation {{id: $id}}) WHERE c.revision = $expected "
        f"SET c.state_json = $state, c.updated_at = timestamp($ts) "
        f"RETURN {_CONV_RETURN}",
        {
            "id": conversation_id,
            "expected": expected_revision,
            "state": encode_state(state),
            "ts": ts_param(),
        },
    )
    if updated is None:
        raise ConversationConflictError("conversation revision conflict")
    return _row_to_conversation(updated)


def delete_conversation(conn: kuzu.Connection, conversation_id: str) -> None:
    get_conversation(conn, conversation_id)
    if count_pending_turns(conn, conversation_id):
        raise ConversationBusyError("conversation has a pending turn")
    conn.execute(
        "MATCH (t:Turn {conversation_id: $id}) DELETE t", {"id": conversation_id}
    )
    conn.execute(
        "MATCH (c:Conversation {id: $id}) DELETE c", {"id": conversation_id}
    )


def count_conversations_for_snapshot(
    conn: kuzu.Connection, snapshot_id: str
) -> int:
    row = fetch_one(
        conn,
        "MATCH (c:Conversation {snapshot_id: $sid}) RETURN count(c)",
        {"sid": snapshot_id},
    )
    return int(row[0]) if row else 0


def count_conversations_for_repository(
    conn: kuzu.Connection, repository_id: str
) -> int:
    row = fetch_one(
        conn,
        "MATCH (c:Conversation {repository_id: $rid}) RETURN count(c)",
        {"rid": repository_id},
    )
    return int(row[0]) if row else 0
