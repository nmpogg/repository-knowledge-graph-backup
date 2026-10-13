"""Redaction and deterministic turn identity."""

from __future__ import annotations

import hashlib

from rkg.conversations.identity import deterministic_turn_id, request_fingerprint
from rkg.conversations.redaction import redact_conversation_text, redact_json_value


def test_turn_id_is_full_sha256() -> None:
    conversation_id = "conv_demo"
    request_id = "req-1"
    digest = hashlib.sha256(f"{conversation_id}:{request_id}".encode()).hexdigest()
    turn_id = deterministic_turn_id(conversation_id, request_id)
    assert turn_id == f"turn_{digest}"
    assert len(digest) == 64
    assert turn_id == turn_id.lower()


def test_same_body_hash_is_stable_and_distinct() -> None:
    first = request_fingerprint("hỏi bảng", None)
    assert first == request_fingerprint("hỏi bảng", None)
    assert first != request_fingerprint("hỏi bảng", "root")
    assert first != request_fingerprint("hỏi event", None)


def test_redaction_removes_forbidden_fragments_and_keeps_prose() -> None:
    raw = (
        "API này ghi bảng nào? password=s3cr3t-value "
        "Bearer sk-test-sentinel-value "
        "AKIAIOSFODNN7EXAMPLE "
        "C:\\Users\\secret\\repo\\app.py "
        "```\ndef leak():\n    return 1\n``` "
        "<think>hidden reasoning</think> "
        "chain of thought: do not store this plan.\n\n"
        "<script>alert(1)</script> keep-me"
    )
    cleaned = redact_conversation_text(raw)
    assert "API này ghi bảng nào?" in cleaned
    assert "keep-me" in cleaned
    for forbidden in (
        "s3cr3t-value",
        "sk-test-sentinel-value",
        "AKIAIOSFODNN7EXAMPLE",
        "Users",
        "def leak",
        "hidden reasoning",
        "do not store",
        "<script",
        "alert(1)",
    ):
        assert forbidden not in cleaned
    assert redact_conversation_text(cleaned) == cleaned
    assert "@@rkg-detail@@" in redact_conversation_text("lead\n\n@@rkg-detail@@\n\ntail")
    assert "<!--rkg-detail-->" not in redact_conversation_text("lead\n\n<!--rkg-detail-->\n\ntail")


def test_json_redaction_drops_reasoning_and_secrets() -> None:
    cleaned = redact_json_value(
        {
            "text": "password=s3cr3t-value",
            "chain_of_thought": "private plan",
            "nested": {"secret": "keep-out"},
        }
    )
    assert cleaned == {"text": "[redacted]", "nested": {}}
