"""Task 19 provider contract, budgets, timeout and wire behavior."""

from __future__ import annotations

import json

import pytest

from rkg.llm import (
    LLMError,
    MockProvider,
    OpenRouterProvider,
    StructuredRequest,
    TurnBudget,
)

SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string", "enum": ["answer", "clarify"]}},
    "required": ["decision"],
    "additionalProperties": False,
}


def _request(**overrides: object) -> StructuredRequest:
    values = {
        "messages": ({"role": "user", "content": "Which API?"},),
        "schema_name": "decision",
        "schema": SCHEMA,
        "max_output_tokens": 100,
    }
    values.update(overrides)
    return StructuredRequest(**values)


def test_mock_enforces_schema_and_shared_model_query_limits() -> None:
    mock = MockProvider([{"decision": "answer"}, {"decision": "clarify"}])
    budget = TurnBudget(max_model_calls=2, max_graph_queries=3)
    for _ in range(3):
        budget.reserve_graph_query()
    with pytest.raises(LLMError, match="llm_budget_exceeded"):
        budget.reserve_graph_query()
    assert mock.complete(_request(), budget).value == {"decision": "answer"}
    assert mock.complete(_request(), budget).value == {"decision": "clarify"}
    with pytest.raises(LLMError, match="llm_budget_exceeded"):
        mock.complete(_request(), budget)
    assert len(mock.requests) == 2


@pytest.mark.parametrize(
    "reply",
    [{"decision": "invent"}, {"decision": "answer", "extra": "bad"}],
)
def test_mock_rejects_nonconforming_output(reply: dict[str, str]) -> None:
    with pytest.raises(LLMError, match="llm_malformed_response"):
        MockProvider([reply]).complete(_request(), TurnBudget())


def test_preflight_rejects_oversize_input_without_calling_provider() -> None:
    mock = MockProvider([{"decision": "answer"}])
    budget = TurnBudget()
    with pytest.raises(LLMError, match="llm_budget_exceeded"):
        mock.complete(_request(max_input_tokens=1), budget)
    assert budget.model_calls == 0
    assert mock.requests == []


def test_openrouter_sends_structured_request_and_handles_missing_usage(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-credential")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    seen = {}

    def transport(payload, headers, timeout):
        seen.update(payload=payload, headers=headers, timeout=timeout)
        return {
            "choices": [{"finish_reason": "stop", "message": {
                "content": json.dumps({"decision": "answer"})
            }}]
        }

    result = OpenRouterProvider(transport).complete(_request(), TurnBudget())
    assert result.value == {"decision": "answer"}
    assert result.input_tokens > 0 and result.output_tokens > 0
    assert result.cost is None
    assert seen["payload"]["model"] == "openai/gpt-4o-mini"
    assert seen["payload"]["max_completion_tokens"] == 100
    assert seen["payload"]["response_format"]["json_schema"]["strict"] is True
    assert seen["payload"]["provider"]["require_parameters"] is True
    assert seen["headers"]["Authorization"] == "Bearer test-credential"
    assert seen["timeout"] is None


def test_openrouter_model_can_be_selected_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-credential")
    monkeypatch.setenv("OPENROUTER_MODEL", "example/another-model")
    seen = {}

    def transport(payload, _headers, _timeout):
        seen.update(payload)
        return {
            "choices": [{"finish_reason": "stop", "message": {
                "content": '{"decision":"answer"}'
            }}]
        }

    result = OpenRouterProvider(transport).complete(_request(), TurnBudget())
    assert seen["model"] == "example/another-model"
    assert result.model == "example/another-model"


def test_openrouter_disabled_does_not_call_transport(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    called = False

    def transport(*_args):
        nonlocal called
        called = True
        return {}

    with pytest.raises(LLMError, match="llm_disabled"):
        OpenRouterProvider(transport).complete(_request(), TurnBudget())
    assert called is False


def test_timeout_is_per_turn_and_raw_transport_error_is_hidden(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-credential")
    tick = [0.0]
    budget = TurnBudget(timeout_seconds=30, started_at=0.0, clock=lambda: tick[0])

    def slow(_payload, _headers, timeout):
        assert timeout == 30
        tick[0] = 31.0
        return {"choices": [{"finish_reason": "stop", "message": {
            "content": '{"decision":"answer"}'
        }}]}

    with pytest.raises(LLMError, match="llm_timeout"):
        OpenRouterProvider(slow).complete(_request(), budget)

    def leaking(_payload, _headers, _timeout):
        raise RuntimeError("credential=secret-example")

    with pytest.raises(LLMError) as error:
        OpenRouterProvider(leaking).complete(_request(), TurnBudget())
    assert error.value.code == "llm_provider_error"
    assert "secret-example" not in str(error.value)


def test_reported_output_usage_cannot_exceed_budget(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-credential")

    def transport(*_args):
        return {
            "choices": [{"finish_reason": "stop", "message": {
                "content": '{"decision":"answer"}'
            }}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 101, "cost": 0.001},
        }

    with pytest.raises(LLMError, match="llm_budget_exceeded"):
        OpenRouterProvider(transport).complete(_request(), TurnBudget())


def test_socket_timeout_maps_to_stable_code(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-credential")

    def transport(*_args):
        raise TimeoutError("provider timeout with sensitive content")

    with pytest.raises(LLMError, match="llm_timeout"):
        OpenRouterProvider(transport).complete(_request(), TurnBudget())
