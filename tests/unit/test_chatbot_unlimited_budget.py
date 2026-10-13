"""No application ceilings by default; protocol/schema guards still apply."""

import json

import pytest

from rkg.llm import MockProvider, OpenRouterProvider, StructuredRequest, TurnBudget

SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
    "additionalProperties": False,
}


def test_default_budget_accepts_large_input_output_and_many_calls():
    request = StructuredRequest(
        messages=({"role": "user", "content": "input " * 10000},),
        schema_name="synthetic",
        schema=SCHEMA,
    )
    provider = MockProvider([{"text": "output " * 3000}] * 5)
    budget = TurnBudget()
    for _ in range(10):
        budget.reserve_graph_query()
    for _ in range(5):
        result = provider.complete(request, budget)
        assert result.input_tokens > 8000
        assert result.output_tokens > 1500
    assert budget.model_calls == 5
    assert budget.graph_queries == 10


def test_default_deadline_is_absent_and_usage_survives_slow_transport(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic")
    tick = [0.0]
    budget = TurnBudget(started_at=0, clock=lambda: tick[0])
    seen = {}

    def transport(payload, _headers, timeout):
        seen.update(payload=payload, timeout=timeout)
        tick[0] = 1000
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps({"text": "synthetic"})},
                }
            ],
            "usage": {"prompt_tokens": 10000, "completion_tokens": 5000},
        }

    request = StructuredRequest(
        messages=({"role": "user", "content": "synthetic"},),
        schema_name="synthetic",
        schema=SCHEMA,
    )
    result = OpenRouterProvider(transport).complete(request, budget)
    assert seen["timeout"] is None
    assert "max_completion_tokens" not in seen["payload"]
    assert result.output_tokens == 5000
    assert budget.remaining_seconds() is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("9" * 5000, -1),
        ("９" * 5000, -1),
        ("0" * 5000 + "2", 1),
        ("٠" * 5000 + "٢", 1),
        ("-" + "0" * 5000 + "2", -1),
        ("0" * 5000, -1),
    ],
    ids=[
        "huge-ascii",
        "huge-fullwidth",
        "padded-ascii",
        "padded-arabic",
        "negative",
        "zero",
    ],
)
def test_numeric_selection_has_no_giant_integer_conversion(text, expected):
    from rkg.conversations.grounded import _candidate_ordinal

    assert _candidate_ordinal(text) == expected
