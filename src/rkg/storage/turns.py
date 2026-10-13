"""Turn rows. Callers pass already-redacted text; this module does not log it."""

from __future__ import annotations

from typing import Any

import kuzu

from rkg.storage._util import dumps_json, fetch_all, fetch_one, loads_json, ts_param
from rkg.storage.conversation_json import (
    encode_response_metadata,
    read_response_metadata,
)
from rkg.storage.errors import NotFoundError
from rkg.storage.oplog import log_operation
from rkg.storage.records import TurnRecord

_TURN_RETURN = (
    "t.id, t.conversation_id, t.sequence, t.client_request_id, t.request_hash, "
    "t.question, t.resolved_question, t.status, t.answer, t.claims_json, "
    "t.citations_json, t.context_turn_ids, t.usage_json, t.error_code, "
    "t.created_at, t.updated_at, t.response_metadata_json"
)

_TERMINAL_RECOVERY = "interrupted"


def _as_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(str(item) for item in value)


def _row_to_turn(row: list[Any]) -> TurnRecord:
    (
        turn_id,
        conversation_id,
        sequence,
        client_request_id,
        request_hash,
        question,
        resolved_question,
        status,
        answer,
        claims_json,
        citations_json,
        context_turn_ids,
        usage_json,
        error_code,
        created_at,
        updated_at,
        response_metadata_json,
    ) = row
    claims = loads_json(claims_json, default=None)
    citations = loads_json(citations_json, default=None)
    return TurnRecord(
        id=turn_id,
        conversation_id=conversation_id,
        sequence=int(sequence),
        client_request_id=client_request_id,
        request_hash=request_hash,
        question=question or "",
        resolved_question=resolved_question,
        status=status,
        answer=answer,
        claims=claims,
        citations=citations,
        context_turn_ids=_as_tuple(context_turn_ids),
        usage=loads_json(usage_json, default=None),
        error_code=error_code,
        created_at=created_at,
        updated_at=updated_at,
        response_metadata=read_response_metadata(
            response_metadata_json, status=status, has_facts=bool(claims or citations),
        ),
    )


def find_turn(conn: kuzu.Connection, turn_id: str) -> TurnRecord | None:
    row = fetch_one(
        conn,
        f"MATCH (t:Turn {{id: $id}}) RETURN {_TURN_RETURN}",
        {"id": turn_id},
    )
    if row is None:
        return None
    return _row_to_turn(row)


def get_turn(conn: kuzu.Connection, turn_id: str) -> TurnRecord:
    found = find_turn(conn, turn_id)
    if found is None:
        raise NotFoundError("turn not found")
    return found


def list_turns(conn: kuzu.Connection, conversation_id: str) -> tuple[TurnRecord, ...]:
    rows = fetch_all(
        conn,
        f"MATCH (t:Turn {{conversation_id: $cid}}) RETURN {_TURN_RETURN} "
        f"ORDER BY t.sequence ASC, t.id ASC",
        {"cid": conversation_id},
    )
    return tuple(_row_to_turn(row) for row in rows)


def next_sequence(conn: kuzu.Connection, conversation_id: str) -> int:
    row = fetch_one(
        conn,
        "MATCH (t:Turn {conversation_id: $cid}) RETURN max(t.sequence)",
        {"cid": conversation_id},
    )
    if row is None or row[0] is None:
        return 1
    return int(row[0]) + 1


def insert_pending_turn(
    conn: kuzu.Connection,
    *,
    turn_id: str,
    conversation_id: str,
    sequence: int,
    client_request_id: str,
    request_hash: str,
    question: str,
) -> TurnRecord:
    now = ts_param()
    conn.execute(
        "CREATE (t:Turn {"
        "id: $id, conversation_id: $cid, sequence: $seq, "
        "client_request_id: $req, request_hash: $hash, question: $question, "
        "resolved_question: null, status: 'pending', answer: null, "
        "claims_json: null, citations_json: null, context_turn_ids: $ctx, "
        "usage_json: null, error_code: null, "
        "created_at: timestamp($ts), updated_at: timestamp($ts)})",
        {
            "id": turn_id,
            "cid": conversation_id,
            "seq": sequence,
            "req": client_request_id,
            "hash": request_hash,
            "question": question,
            "ctx": [],
            "ts": now,
        },
    )
    return get_turn(conn, turn_id)


def finalize_turn(
    conn: kuzu.Connection,
    turn_id: str,
    *,
    status: str,
    resolved_question: str | None,
    answer: str | None,
    claims: list[Any] | None,
    citations: list[Any] | None,
    context_turn_ids: tuple[str, ...],
    usage: dict[str, Any] | None,
    error_code: str | None,
    response_metadata: dict[str, Any] | None = None,
) -> TurnRecord:
    metadata_json = encode_response_metadata(
        response_metadata, status=status, has_facts=bool(claims or citations),
    )
    row = fetch_one(
        conn,
        f"MATCH (t:Turn {{id: $id}}) "
        f"SET t.status = $status, t.resolved_question = $resolved, "
        f"t.answer = $answer, t.claims_json = $claims, "
        f"t.citations_json = $citations, t.context_turn_ids = $ctx, "
        f"t.usage_json = $usage, t.error_code = $err, "
        f"t.response_metadata_json = $metadata, "
        f"t.updated_at = timestamp($ts) "
        f"RETURN {_TURN_RETURN}",
        {
            "id": turn_id,
            "status": status,
            "resolved": resolved_question,
            "answer": answer,
            "claims": dumps_json(claims) if claims is not None else None,
            "citations": dumps_json(citations) if citations is not None else None,
            "ctx": list(context_turn_ids),
            "usage": dumps_json(usage) if usage is not None else None,
            "err": error_code,
            "metadata": metadata_json,
            "ts": ts_param(),
        },
    )
    if row is None:
        raise NotFoundError("turn not found")
    return _row_to_turn(row)


def recover_pending_turns(conn: kuzu.Connection) -> tuple[str, ...]:
    """Restart recovery: pending turns become interrupted. Focus is untouched."""
    rows = fetch_all(
        conn,
        "MATCH (t:Turn {status: 'pending'}) RETURN t.id, t.conversation_id "
        "ORDER BY t.id ASC",
    )
    recovered: list[str] = []
    now = ts_param()
    for turn_id, conversation_id in rows:
        conn.execute(
            "MATCH (t:Turn {id: $id}) "
            "SET t.status = $status, t.error_code = $err, "
            "t.updated_at = timestamp($ts)",
            {
                "id": turn_id,
                "status": _TERMINAL_RECOVERY,
                "err": _TERMINAL_RECOVERY,
                "ts": now,
            },
        )
        recovered.append(str(turn_id))
        log_operation(
            "turn_recovered",
            conversation_id=str(conversation_id),
            turn_id=str(turn_id),
            status=_TERMINAL_RECOVERY,
            error_code=_TERMINAL_RECOVERY,
        )
    return tuple(recovered)
