"""Exact persisted citation resolution. No entity evidence substitution or source."""

from __future__ import annotations

from typing import Any

from rkg.conversations.narrative import safe_location
from rkg.graph.access import load_evidence_by_ids, require_readable_snapshot
from rkg.storage import Storage
from rkg.storage.errors import NotFoundError
from rkg.storage.turns import get_turn


def exact_citation(
    storage: Storage, conversation_id: str, turn_id: str, index: int
) -> dict[str, Any]:
    conversation = storage.get_conversation(conversation_id)
    storage.get_repository(conversation.repository_id)
    turn = get_turn(storage.conn, turn_id)
    if turn.conversation_id != conversation.id:
        raise NotFoundError("citation unavailable")
    citations = turn.citations or []
    if not 0 <= index < len(citations):
        raise NotFoundError("citation unavailable")
    citation = citations[index]
    if (
        not isinstance(citation, dict)
        or citation.get("snapshot_id") != conversation.snapshot_id
    ):
        raise NotFoundError("citation unavailable")
    evidence_id = citation.get("evidence_id")
    if not isinstance(evidence_id, str) or not evidence_id:
        raise NotFoundError("citation unavailable")
    snap = require_readable_snapshot(
        storage, conversation.repository_id, conversation.snapshot_id
    )
    with storage.pin_reader(conversation.repository_id, snap.id):
        items = load_evidence_by_ids(storage, snap.id, {evidence_id})
        if len(items) != 1:
            raise NotFoundError("citation unavailable")
        evidence = items[0]
        if (
            not safe_location(evidence.file_path)
            or len(evidence.file_path) > 2000
            or not 0 < len(evidence.rule) <= 200
            or not 0 < len(evidence.id) <= 200
        ):
            raise NotFoundError("citation unavailable")
        filesystem = evidence.rule == "RKG.structure.contains.v1"
        if not filesystem and not 0 < evidence.start_line <= evidence.end_line:
            raise NotFoundError("citation unavailable")
        return {
            "schema_version": "rkg.citation/1",
            "conversation_id": conversation.id,
            "turn_id": turn.id,
            "snapshot_id": snap.id,
            "citation_index": index,
            "evidence": {
                "id": evidence.id,
                "file_path": evidence.file_path,
                "provenance": "filesystem" if filesystem else "source",
                "start_line": None if filesystem else evidence.start_line,
                "end_line": None if filesystem else evidence.end_line,
                "rule": evidence.rule,
            },
        }
