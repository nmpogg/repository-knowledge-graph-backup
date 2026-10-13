"""Bounded durable metadata/state. No prompt, transcript or JSON in errors."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from rkg.storage._util import EDGE_REL_TABLE, dumps_json

MAX_METADATA_BYTES = 8192
MAX_STATE_BYTES = 32768
_WIRE_SCHEMA = (
    Path(__file__).resolve().parents[3]
    / ".aide/tech-specs/RKG-TRANSPORT/api"
    / "SCH-RKG-CONVERSATION-v1.json"
)
_KINDS = {
    "answered": {"answer", "greeting"},
    "needs_clarification": {"clarification"},
    "insufficient_evidence": {"insufficient"},
    "failed": {"error"},
    "interrupted": {"error"},
}
_RETRIEVAL_LIMITS = {"max_chars", "max_nodes", "max_edges", "max_depth"}
_INTENT_KEYS = {
    "question",
    "ui_locale",
    "language",
    "relation_types",
    "direction",
    "entity_type",
    "candidate_ids",
}


class ConversationJSONError(ValueError):
    def __init__(self, code: str = "llm_malformed_response") -> None:
        self.code = code
        super().__init__(code)


@cache
def _metadata_validator() -> Draft202012Validator:
    schema = json.loads(_WIRE_SCHEMA.read_text(encoding="utf-8"))
    return Draft202012Validator(
        {
            "$defs": schema["$defs"],
            "$ref": "#/$defs/ResponseMetadata",
        }
    )


def _bounded_json(value: Any, limit: int) -> str:
    try:
        raw = dumps_json(value)
    except (TypeError, ValueError):
        raise ConversationJSONError() from None
    if len(raw.encode("utf-8")) > limit:
        raise ConversationJSONError("llm_budget_exceeded")
    return raw


def encode_response_metadata(
    value: dict[str, Any] | None,
    *,
    status: str,
    has_facts: bool,
) -> str | None:
    if value is None:
        return None  # Legacy result: never invent flags or completeness.
    raw = _bounded_json(value, MAX_METADATA_BYTES)
    if not _metadata_validator().is_valid(value):
        raise ConversationJSONError()
    kind, coverage = value["kind"], value["coverage"]
    retrieval, history = value["retrieval_truncated"], value["history_truncated"]
    limits = set(value["limitations"])
    if kind not in _KINDS.get(status, set()):
        raise ConversationJSONError()
    if (kind == "insufficient") != (value["insufficient_reason"] is not None):
        raise ConversationJSONError()
    if kind == "answer" and (
        value["subject"] is None
        or not isinstance(retrieval, bool)
        or not isinstance(history, bool)
        or coverage not in {"complete", "partial"}
    ):
        raise ConversationJSONError()
    if kind in {"greeting", "clarification", "insufficient"} and has_facts:
        raise ConversationJSONError()
    if kind == "greeting" and value["subject"] is not None:
        raise ConversationJSONError()
    if kind in {"greeting", "clarification"} and coverage != "not_applicable":
        raise ConversationJSONError()
    if bool(limits & _RETRIEVAL_LIMITS) != (retrieval is True):
        raise ConversationJSONError()
    if ("history_truncated" in limits) != (history is True):
        raise ConversationJSONError()
    if coverage == "complete" and (
        retrieval is not False or history is not False or limits
    ):
        raise ConversationJSONError()
    if coverage == "partial" and not (retrieval is True or history is True):
        raise ConversationJSONError()
    if kind in {"answer", "insufficient"} and (retrieval is True or history is True):
        if coverage != "partial":
            raise ConversationJSONError()
    return raw


def read_response_metadata(
    raw: str | None,
    *,
    status: str,
    has_facts: bool,
) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        if len(raw.encode("utf-8")) > MAX_METADATA_BYTES:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("version") != 1:
            return None  # Future version is unknown; stored bytes stay untouched.
        encode_response_metadata(value, status=status, has_facts=has_facts)
        return value
    except (ValueError, TypeError):
        return None


def _ordered_ids(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= 20
        and all(isinstance(i, str) and 0 < len(i) <= 200 for i in value)
        and len(value) == len(set(value))
    )


def encode_state(state: dict[str, Any]) -> str:
    if not isinstance(state, dict):
        raise ConversationJSONError()
    # Original question text has no character ceiling; bound structural state only.
    envelope = dict(state)
    intent_value = envelope.get("pending_intent")
    if isinstance(intent_value, dict):
        envelope["pending_intent"] = {**intent_value, "question": ""}
    _bounded_json(envelope, MAX_STATE_BYTES)
    try:
        raw = dumps_json(state)
    except (TypeError, ValueError):
        raise ConversationJSONError() from None
    if "state_version" not in state:
        return raw  # Readable legacy state; do not infer its original question.
    if state["state_version"] != 2:
        raise ConversationJSONError()
    pending = state.get("pending_candidate_ids")
    if not _ordered_ids(pending):
        raise ConversationJSONError()
    intent = state.get("pending_intent")
    if intent is None:
        return raw  # Includes legacy pending IDs without a recoverable intent.
    if not isinstance(intent, dict) or set(intent) != _INTENT_KEYS:
        raise ConversationJSONError()
    question, relations = intent["question"], intent["relation_types"]
    if not (
        isinstance(question, str)
        and question.strip() == question
        and len(question) > 0
        and intent["ui_locale"] in ("vi", "en")
        and intent["language"] in ("vi", "en")
        and intent["direction"] in ("incoming", "outgoing")
        and intent["entity_type"]
        in (
            "any",
            "Directory",
            "SourceUnit",
            "Namespace",
            "Type",
            "Callable",
            "Endpoint",
            "DataResource",
            "MessageChannel",
            "Configuration",
            "ExternalDependency",
        )
        and isinstance(relations, list)
        and all(isinstance(r, str) and r in EDGE_REL_TABLE for r in relations)
        and len(relations) == len(set(relations))
        and _ordered_ids(intent["candidate_ids"])
        and intent["candidate_ids"] == pending
    ):
        raise ConversationJSONError()
    return raw
