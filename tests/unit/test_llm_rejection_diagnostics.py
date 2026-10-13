"""Safe stage/reason codes identify rejection without recording provider data."""

import logging

import pytest

from rkg.llm import LLMError, StructuredRequest, TurnBudget
from rkg.llm.diagnostics import log_rejection
from rkg.llm.provider import parse_response

SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
    "additionalProperties": False,
}


@pytest.mark.parametrize(
    "content,reason",
    [
        (None, "invalid_content"),
        ("not-json-synthetic", "invalid_json"),
        ('{"ok":"wrong"}', "invalid_schema"),
    ],
)
def test_parse_failure_has_safe_reason(content, reason):
    req = StructuredRequest(
        messages=({"role": "user", "content": "synthetic-private-question"},),
        schema_name="synthetic",
        schema=SCHEMA,
    )
    with pytest.raises(LLMError) as exc:
        parse_response(content, req, TurnBudget(), input_tokens=1, model="synthetic")
    assert exc.value.code == "llm_malformed_response"
    assert exc.value.reason == reason
    assert str(exc.value) == "llm_malformed_response"


def test_log_rejection_never_echoes_unrecognized_fields(caplog):
    with caplog.at_level(logging.INFO, logger="rkg.conversation"):
        log_rejection(
            "synthetic-secret-stage",
            "synthetic-secret-response",
            "synthetic-secret-code",
        )
        log_rejection("narrative", "invalid_json", "llm_malformed_response")
    assert "synthetic-secret" not in caplog.text
    assert all(record.levelno == logging.WARNING for record in caplog.records)
    assert (
        "stage=narrative reason=invalid_json error_code=llm_malformed_response"
        in caplog.text
    )


def test_exception_does_not_retain_arbitrary_reason():
    assert LLMError("llm_malformed_response", reason="synthetic-secret").reason is None
