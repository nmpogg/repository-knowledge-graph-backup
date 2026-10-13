"""Conversation persistence: pin, revision, idempotency, redaction, recovery.

HTTP mapping belongs to T-016/T-021. Codes here match API-RKG-CORE-v1:

- ``invalid_turn_request`` → 422 (missing or malformed required fields)
- ``conversation_conflict`` → 409 (stale revision or same key, different body)
- ``conversation_busy`` → 409 (another turn is still pending)
- ``snapshot_unavailable`` → 410 (pinned graph is gone; pin is not moved)
- ``no_active_snapshot`` → 409
"""

from __future__ import annotations

import re
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from rkg.conversations.identity import deterministic_turn_id, request_fingerprint
from rkg.conversations.language import normalize_locale
from rkg.conversations.redaction import redact_conversation_text, redact_json_value
from rkg.graph.errors import NoActiveSnapshotError, SnapshotUnavailableError
from rkg.llm.provider import LLMError
from rkg.storage import turns as turn_store
from rkg.storage.connection import Storage
from rkg.storage.conversation_json import (
    ConversationJSONError,
    encode_response_metadata,
    encode_state,
)
from rkg.storage.conversations import (
    advance_revision,
    count_pending_turns,
    get_conversation,
    write_state,
)
from rkg.storage.errors import (
    ConversationBusyError,
    ConversationConflictError,
    InvalidTurnRequestError,
    NotFoundError,
)
from rkg.storage.oplog import log_operation
from rkg.storage.records import ConversationRecord, TurnRecord

_SUCCESS = frozenset({"answered", "insufficient_evidence", "needs_clarification"})
_TURN_ID = re.compile(r"^turn_[0-9a-f]{64}$")
_USAGE_KEYS = ("input_tokens", "output_tokens", "model_calls")


@dataclass(frozen=True, slots=True)
class TurnContext:
    """Redacted view handed to a later provider. No graph write handle."""

    conversation_id: str
    turn_id: str
    repository_id: str
    snapshot_id: str
    question: str
    root_id: str | None
    focus_entity_id: str | None
    pending_candidate_ids: tuple[str, ...]
    pending_intent: dict[str, Any] | None = None
    ui_locale: str = "vi"


@dataclass(frozen=True, slots=True)
class ProviderResult:
    status: str
    answer: str = ""
    resolved_question: str = ""
    claims: tuple[Any, ...] = ()
    citations: tuple[Any, ...] = ()
    candidate_entity_ids: tuple[str, ...] = ()
    focus_entity_id: str | None = None
    usage: dict[str, Any] | None = None
    context_turn_ids: tuple[str, ...] = ()
    response_metadata: dict[str, Any] | None = None
    pending_intent_update: str | None = None
    pending_intent: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TurnSubmission:
    turn: TurnRecord
    conversation: ConversationRecord
    created: bool


@dataclass(frozen=True, slots=True)
class ConversationView:
    conversation: ConversationRecord
    turns: tuple[TurnRecord, ...]


Provider = Callable[[TurnContext], ProviderResult]


def create_conversation(
    storage: Storage,
    *,
    repository_id: str,
    snapshot_id: str | None = None,
    title: str = "",
    conversation_id: str | None = None,
) -> ConversationRecord:
    """Pin the given snapshot, or the repository active snapshot when omitted."""
    pinned = snapshot_id
    if pinned is None or pinned == "":
        repo = storage.get_repository(repository_id)
        if not repo.active_snapshot_id:
            raise NoActiveSnapshotError("repository has no active snapshot")
        pinned = repo.active_snapshot_id
    return storage.create_conversation(
        repository_id=repository_id,
        snapshot_id=pinned,
        title=redact_conversation_text(title or ""),
        conversation_id=conversation_id,
    )


def list_conversations(
    storage: Storage,
    *,
    repository_id: str | None = None,
    snapshot_id: str | None = None,
    offset: int = 0,
    limit: int = 20,
):
    """Paged summaries. Does not retarget a snapshot pin."""
    return storage.list_conversations(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        offset=offset,
        limit=limit,
    )


def list_turns(storage: Storage, conversation_id: str) -> tuple[TurnRecord, ...]:
    storage.get_conversation(conversation_id)
    return turn_store.list_turns(storage.conn, conversation_id)


def delete_conversation(storage: Storage, conversation_id: str) -> None:
    storage.delete_conversation(conversation_id)


def cleanup_snapshots(storage: Storage, repository_id: str) -> tuple[str, ...]:
    return storage.cleanup_snapshots(repository_id)


def read_conversation(storage: Storage, conversation_id: str) -> ConversationView:
    """Load history for the pinned snapshot. Never retargets the pin."""
    conversation = storage.get_conversation(conversation_id)
    _require_pinned(storage, conversation)
    turns = turn_store.list_turns(storage.conn, conversation.id)
    fresh = storage.get_conversation(conversation_id)
    if fresh.snapshot_id != conversation.snapshot_id:
        raise SnapshotUnavailableError("snapshot graph payload unavailable")
    return ConversationView(conversation=fresh, turns=turns)


def begin_turn(
    storage: Storage,
    conversation_id: str,
    *,
    question: object,
    client_request_id: object,
    expected_revision: object,
    root_id: object = None,
    ui_locale: object = None,
) -> TurnSubmission:
    """Commit a pending turn, or replay the same body. Does not call a provider."""
    try:
        try:
            locale = normalize_locale(ui_locale)
        except ValueError:
            raise InvalidTurnRequestError("turn request is invalid") from None
        body, request_id, revision, root = _validate_turn_fields(
            question=question,
            client_request_id=client_request_id,
            expected_revision=expected_revision,
            root_id=root_id,
        )
    except InvalidTurnRequestError:
        log_operation(
            "turn_rejected",
            conversation_id=str(conversation_id),
            error_code=InvalidTurnRequestError.code,
        )
        raise

    conversation = storage.get_conversation(conversation_id)
    turn_id = deterministic_turn_id(conversation.id, request_id)
    fingerprint = request_fingerprint(body, root, ui_locale=locale)
    existing = turn_store.find_turn(storage.conn, turn_id)
    if existing is not None:
        return _replay_or_conflict(conversation, existing, fingerprint)

    _require_pinned(storage, conversation)
    redacted = redact_conversation_text(body)

    def _accept() -> TurnSubmission:
        current = get_conversation(storage.conn, conversation.id)
        again = turn_store.find_turn(storage.conn, turn_id)
        if again is not None:
            return _replay_or_conflict(current, again, fingerprint)
        if current.revision != revision:
            raise ConversationConflictError("conversation revision conflict")
        if count_pending_turns(storage.conn, conversation.id):
            raise ConversationBusyError("conversation has a pending turn")
        sequence = turn_store.next_sequence(storage.conn, conversation.id)
        pending = turn_store.insert_pending_turn(
            storage.conn,
            turn_id=turn_id,
            conversation_id=conversation.id,
            sequence=sequence,
            client_request_id=request_id,
            request_hash=fingerprint,
            question=redacted,
        )
        updated = advance_revision(storage.conn, conversation.id, revision)
        return TurnSubmission(turn=pending, conversation=updated, created=True)

    try:
        submission = _transaction(storage, _accept)
    except (ConversationConflictError, ConversationBusyError) as exc:
        log_operation(
            "turn_rejected",
            conversation_id=conversation.id,
            turn_id=turn_id,
            error_code=exc.code,
        )
        raise
    if submission.created:
        log_operation(
            "turn_accepted",
            conversation_id=conversation.id,
            turn_id=submission.turn.id,
            status=submission.turn.status,
            revision=submission.conversation.revision,
        )
    return submission


def submit_turn(
    storage: Storage,
    conversation_id: str,
    *,
    question: object,
    client_request_id: object,
    expected_revision: object,
    provider: Provider,
    root_id: object = None,
    ui_locale: object = None,
) -> TurnSubmission:
    """Persist pending, release the write, then finalize from the provider result.

    Validation and conflict paths return before ``provider`` is called. A provider
    failure marks the turn failed and leaves the previous focus in place.
    """
    submission = begin_turn(
        storage,
        conversation_id,
        question=question,
        client_request_id=client_request_id,
        expected_revision=expected_revision,
        root_id=root_id,
        ui_locale=ui_locale,
    )
    if not submission.created:
        return submission
    state = submission.conversation.state or {}
    pending = tuple(str(item) for item in (state.get("pending_candidate_ids") or []))
    focus = state.get("focus_entity_id")
    context = TurnContext(
        conversation_id=submission.conversation.id,
        turn_id=submission.turn.id,
        repository_id=submission.conversation.repository_id,
        snapshot_id=submission.conversation.snapshot_id,
        question=submission.turn.question,
        root_id=root_id if isinstance(root_id, str) else None,
        focus_entity_id=str(focus) if isinstance(focus, str) else None,
        pending_candidate_ids=pending,
        pending_intent=deepcopy(state.get("pending_intent")),
        ui_locale=normalize_locale(ui_locale),
    )
    try:
        result = provider(context)
    except LLMError as exc:
        allowed = {
            "llm_disabled",
            "llm_timeout",
            "llm_budget_exceeded",
            "llm_malformed_response",
            "llm_provider_error",
            "llm_invalid_request",
        }
        return _fail_turn(
            storage, submission, exc.code if exc.code in allowed else "provider_failed"
        )
    except Exception:
        return _fail_turn(storage, submission, "provider_failed")
    if not isinstance(result, ProviderResult) or result.status not in _SUCCESS:
        return _fail_turn(storage, submission, "invalid_provider_status")
    try:
        return _complete_turn(storage, submission, result)
    except ConversationJSONError as exc:
        return _fail_turn(storage, submission, exc.code)


def _replay_or_conflict(
    conversation: ConversationRecord, existing: TurnRecord, fingerprint: str
) -> TurnSubmission:
    if existing.request_hash != fingerprint:
        log_operation(
            "turn_rejected",
            conversation_id=conversation.id,
            turn_id=existing.id,
            error_code=ConversationConflictError.code,
        )
        raise ConversationConflictError("turn request identity conflict")
    log_operation(
        "turn_replayed",
        conversation_id=conversation.id,
        turn_id=existing.id,
        status=existing.status,
        revision=conversation.revision,
    )
    return TurnSubmission(turn=existing, conversation=conversation, created=False)


def _complete_turn(
    storage: Storage, submission: TurnSubmission, result: ProviderResult
) -> TurnSubmission:
    expected = submission.conversation.revision
    pinned = submission.conversation.snapshot_id
    # Reject malformed structure before redaction; never salvage extra provider fields.
    encode_response_metadata(
        result.response_metadata,
        status=result.status,
        has_facts=bool(result.claims or result.citations),
    )
    if result.response_metadata and result.response_metadata.get("kind") == "answer":
        used = set()
        for claim in result.claims:
            if not isinstance(claim, dict) or not isinstance(claim.get("edge_id"), str):
                raise ConversationJSONError()
            indexes = claim.get("citation_indexes")
            if not isinstance(indexes, list) or not indexes:
                raise ConversationJSONError()
            for index in indexes:
                if (
                    isinstance(index, bool)
                    or not isinstance(index, int)
                    or not 0 <= index < len(result.citations)
                ):
                    raise ConversationJSONError()
                citation = result.citations[index]
                if (
                    not isinstance(citation, dict)
                    or citation.get("edge_id") != claim["edge_id"]
                    or citation.get("snapshot_id") != pinned
                    or not isinstance(citation.get("evidence_id"), str)
                    or not citation["evidence_id"]
                    or "quote" in citation
                ):
                    raise ConversationJSONError()
                used.add(index)
        if used != set(range(len(result.citations))):
            raise ConversationJSONError()
    metadata = redact_json_value(result.response_metadata)
    state = _next_state(submission.conversation.state, result)
    encode_state(state)
    answer = redact_conversation_text(result.answer or "")
    resolved = redact_conversation_text(result.resolved_question or "")
    claims = redact_json_value(list(result.claims))
    citations = _citations(result.citations, pinned)
    context_ids = tuple(
        item for item in result.context_turn_ids if _TURN_ID.fullmatch(item)
    )
    usage = _usage(result.usage)

    def _apply() -> TurnSubmission:
        current = get_conversation(storage.conn, submission.conversation.id)
        if current.revision != expected or current.snapshot_id != pinned:
            raise ConversationConflictError("conversation revision conflict")
        turn = turn_store.finalize_turn(
            storage.conn,
            submission.turn.id,
            status=result.status,
            resolved_question=resolved,
            answer=answer,
            claims=claims if isinstance(claims, list) else None,
            citations=citations,
            context_turn_ids=context_ids,
            usage=usage,
            error_code=None,
            response_metadata=metadata,
        )
        updated = write_state(
            storage.conn,
            current.id,
            expected_revision=expected,
            state=state,
        )
        return TurnSubmission(turn=turn, conversation=updated, created=True)

    try:
        done = _transaction(storage, _apply)
    except ConversationConflictError:
        log_operation(
            "turn_rejected",
            conversation_id=submission.conversation.id,
            turn_id=submission.turn.id,
            error_code=ConversationConflictError.code,
        )
        raise
    log_operation(
        "turn_finalized",
        conversation_id=done.conversation.id,
        turn_id=done.turn.id,
        status=done.turn.status,
        revision=done.conversation.revision,
    )
    return done


def _fail_turn(
    storage: Storage, submission: TurnSubmission, error_code: str
) -> TurnSubmission:
    expected = submission.conversation.revision
    pinned = submission.conversation.snapshot_id

    def _apply() -> TurnSubmission:
        current = get_conversation(storage.conn, submission.conversation.id)
        if current.revision != expected or current.snapshot_id != pinned:
            raise ConversationConflictError("conversation revision conflict")
        turn = turn_store.finalize_turn(
            storage.conn,
            submission.turn.id,
            status="failed",
            resolved_question=None,
            answer=None,
            claims=None,
            citations=None,
            context_turn_ids=(),
            usage=None,
            error_code=error_code,
        )
        return TurnSubmission(turn=turn, conversation=current, created=True)

    done = _transaction(storage, _apply)
    log_operation(
        "turn_failed",
        conversation_id=done.conversation.id,
        turn_id=done.turn.id,
        status="failed",
        error_code=error_code,
        revision=done.conversation.revision,
    )
    return done


def _require_pinned(storage: Storage, conversation: ConversationRecord) -> None:
    try:
        snap = storage.get_snapshot(
            conversation.repository_id, conversation.snapshot_id
        )
    except NotFoundError:
        raise SnapshotUnavailableError("snapshot graph payload unavailable") from None
    if snap.status != "ready" or snap.id != conversation.snapshot_id:
        raise SnapshotUnavailableError("snapshot graph payload unavailable")


def _validate_turn_fields(
    *,
    question: object,
    client_request_id: object,
    expected_revision: object,
    root_id: object,
) -> tuple[str, str, int, str | None]:
    if (
        not isinstance(question, str)
        or not question.strip()
    ):
        raise InvalidTurnRequestError("turn request is invalid")
    if not isinstance(client_request_id, str) or not client_request_id.strip():
        raise InvalidTurnRequestError("turn request is invalid")
    if (
        isinstance(expected_revision, bool)
        or not isinstance(expected_revision, int)
        or expected_revision < 1
    ):
        raise InvalidTurnRequestError("turn request is invalid")
    if root_id is not None and not isinstance(root_id, str):
        raise InvalidTurnRequestError("turn request is invalid")
    return question, client_request_id, expected_revision, root_id


def _next_state(state: dict[str, Any] | None, result: ProviderResult) -> dict[str, Any]:
    current = state or {}
    focus = current.get("focus_entity_id")
    pending = list(current.get("pending_candidate_ids") or [])
    action = result.pending_intent_update
    if action is not None and (
        not isinstance(action, str) or action not in {"preserve", "replace", "clear"}
    ):
        raise ConversationJSONError()
    updated = dict(current)
    if result.response_metadata and result.response_metadata.get("kind") == "greeting":
        if (
            action not in {None, "preserve"}
            or result.focus_entity_id not in (None, focus)
            or result.candidate_entity_ids
            or result.pending_intent is not None
        ):
            raise ConversationJSONError()
        return updated  # Intrinsic greeting invariant, even with an omitted action.
    if action == "preserve":
        return updated
    if action == "replace":
        if result.status != "needs_clarification" or not isinstance(
            result.pending_intent, dict
        ):
            raise ConversationJSONError()
        pending = list(result.candidate_entity_ids)
        intent = dict(result.pending_intent)
        if isinstance(intent.get("question"), str):
            intent["question"] = intent["question"].strip()
        # Validate all fields before redaction can drop a forbidden/unknown key.
        encode_state(
            {
                "state_version": 2,
                "focus_entity_id": focus,
                "pending_candidate_ids": pending,
                "pending_intent": intent,
            }
        )
        intent = redact_json_value(intent)
        updated.update(state_version=2, pending_intent=intent)
    elif action == "clear":
        if result.status == "needs_clarification":
            raise ConversationJSONError()
        pending = []
        updated.update(state_version=2, pending_intent=None)
    elif result.status == "needs_clarification":
        pending = [str(item) for item in result.candidate_entity_ids]
        if "pending_intent" in updated:
            updated["pending_intent"] = None
    if result.status == "answered" and result.focus_entity_id:
        focus = str(result.focus_entity_id)
        pending = []
        if "pending_intent" in updated:
            updated["pending_intent"] = None
    updated.update(focus_entity_id=focus, pending_candidate_ids=pending)
    return updated


def _citations(raw: tuple[Any, ...], pinned_snapshot: str) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        foreign = item.get("snapshot_id")
        if isinstance(foreign, str) and foreign and foreign != pinned_snapshot:
            continue
        entry: dict[str, str] = {"snapshot_id": pinned_snapshot}
        for key in ("entity_id", "evidence_id", "edge_id"):
            value = item.get(key)
            if isinstance(value, str) and value:
                entry[key] = value
        quote = item.get("quote")
        if isinstance(quote, str) and quote:
            entry["quote"] = redact_conversation_text(quote)
        cleaned.append(entry)
    return cleaned


def _usage(raw: dict[str, Any] | None) -> dict[str, int] | None:
    if not isinstance(raw, dict):
        return None
    kept: dict[str, int] = {}
    for key in _USAGE_KEYS:
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            continue
        kept[key] = value
    return kept or None


def _transaction(
    storage: Storage, body: Callable[[], TurnSubmission]
) -> TurnSubmission:
    storage.conn.execute("BEGIN TRANSACTION")
    try:
        result = body()
    except Exception:
        storage.conn.execute("ROLLBACK")
        raise
    storage.conn.execute("COMMIT")
    return result
