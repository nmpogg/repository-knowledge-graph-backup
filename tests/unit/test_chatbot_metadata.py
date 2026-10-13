"""Semantic/boundary validation of durable chatbot JSON, not schema mirroring."""

from copy import deepcopy

import pytest

from rkg.storage.conversation_json import (
    ConversationJSONError,
    encode_response_metadata,
    encode_state,
)


def _answer():
    return {
        "version": 1,
        "language": "vi",
        "kind": "answer",
        "subject": {
            "entity_id": "root",
            "type": "Callable",
            "name": "login",
            "qualified_name": "app.login",
            "method": None,
            "path": None,
        },
        "coverage": "complete",
        "retrieval_truncated": False,
        "history_truncated": False,
        "limitations": [],
        "insufficient_reason": None,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "clarification"},
        {"subject": None},
        {"history_truncated": None},
        {"coverage": "unknown"},
        {"coverage": "not_applicable"},
        {
            "coverage": "complete",
            "retrieval_truncated": True,
            "limitations": ["max_nodes"],
        },
        {"coverage": "partial"},
        {"coverage": "partial", "retrieval_truncated": True, "limitations": []},
        {"limitations": ["history_truncated"]},
        {"insufficient_reason": "intent_unresolved"},
    ],
)
def test_inconsistent_metadata_rejected(changes):
    meta = {**_answer(), **changes}
    with pytest.raises(ConversationJSONError) as err:
        encode_response_metadata(meta, status="answered", has_facts=True)
    assert err.value.code == "llm_malformed_response"


def test_partial_metadata_requires_observed_matching_limits():
    meta = {
        **_answer(),
        "coverage": "partial",
        "retrieval_truncated": True,
        "history_truncated": True,
        "limitations": ["max_edges", "history_truncated"],
    }
    assert '"coverage":"partial"' in encode_response_metadata(
        meta, status="answered", has_facts=True
    )


def test_greeting_cannot_store_factual_claims():
    meta = {
        **_answer(),
        "kind": "greeting",
        "subject": None,
        "coverage": "not_applicable",
        "retrieval_truncated": None,
    }
    with pytest.raises(ConversationJSONError):
        encode_response_metadata(meta, status="answered", has_facts=True)


@pytest.mark.parametrize(
    "kind,status",
    [
        ("clarification", "needs_clarification"),
        ("insufficient", "insufficient_evidence"),
    ],
)
def test_guidance_cannot_store_facts(kind, status):
    meta = {
        **_answer(),
        "kind": kind,
        "subject": None,
        "coverage": "not_applicable" if kind == "clarification" else "unknown",
        "retrieval_truncated": None,
        "history_truncated": None,
        "insufficient_reason": "intent_unresolved" if kind == "insufficient" else None,
    }
    with pytest.raises(ConversationJSONError):
        encode_response_metadata(meta, status=status, has_facts=True)
    assert encode_response_metadata(meta, status=status, has_facts=False)


def test_metadata_byte_limit_is_utf8_not_character_count():
    meta = deepcopy(_answer())
    meta["subject"].update(name="界" * 1900, qualified_name="界" * 1900)
    with pytest.raises(ConversationJSONError) as err:
        encode_response_metadata(meta, status="answered", has_facts=True)
    assert err.value.code == "llm_budget_exceeded"


def _state():
    return {
        "state_version": 2,
        "focus_entity_id": None,
        "pending_candidate_ids": ["b", "a"],
        "pending_intent": {
            "question": "fixture",
            "ui_locale": "vi",
            "language": "vi",
            "direction": "outgoing",
            "entity_type": "Endpoint",
            "relation_types": ["calls"],
            "candidate_ids": ["b", "a"],
        },
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"candidate_ids": ["a", "b"]},
        {"candidate_ids": ["b", "b"]},
        {"question": ""},
        {"language": "fr"},
        {"direction": "both"},
        {"entity_type": "Unknown"},
        {"relation_types": ["execute"]},
        {"relation_types": ["calls", "calls"]},
        {"raw_source": "fixture"},
    ],
)
def test_pending_intent_rejects_order_mismatch_and_unbounded_fields(changes):
    state = _state()
    state["pending_intent"].update(changes)
    with pytest.raises(ConversationJSONError):
        encode_state(state)


def test_state_limit_and_legacy_state_are_explicit():
    assert encode_state({"focus_entity_id": None, "pending_candidate_ids": ["old"]})
    with pytest.raises(ConversationJSONError) as err:
        encode_state({"focus_entity_id": "x" * 33000, "pending_candidate_ids": []})
    assert err.value.code == "llm_budget_exceeded"
