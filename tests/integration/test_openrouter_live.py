"""Optional live smoke test. Run with OPENROUTER_API_KEY set server-side."""

from __future__ import annotations

import os

import pytest

from rkg.llm import OpenRouterProvider, StructuredRequest, TurnBudget


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OpenRouter credential unavailable"
)
def test_openrouter_live_structured_response() -> None:
    request = StructuredRequest(
        messages=({"role": "user", "content": "Return the value ready."},),
        schema_name="health",
        schema={
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ready"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
        max_output_tokens=100,
    )
    budget = TurnBudget()
    result = OpenRouterProvider().complete(request, budget)
    assert result.value == {"status": "ready"}
    assert budget.model_calls == 1
    assert 0 < result.output_tokens <= 100
