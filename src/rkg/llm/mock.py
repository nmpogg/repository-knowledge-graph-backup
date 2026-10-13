"""Deterministic structured provider for caller contract tests."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from rkg.llm.provider import (
    LLMError,
    StructuredRequest,
    StructuredResponse,
    TurnBudget,
    parse_response,
    prepare_call,
)


class MockProvider:
    def __init__(self, responses: Iterable[Mapping[str, Any]]) -> None:
        self._responses = iter(responses)
        self.requests: list[StructuredRequest] = []

    def complete(
        self, request: StructuredRequest, budget: TurnBudget
    ) -> StructuredResponse:
        input_tokens, _ = prepare_call(request, budget)
        self.requests.append(request)
        try:
            value = next(self._responses)
        except StopIteration:
            raise LLMError("llm_provider_error") from None
        return parse_response(
            json.dumps(value, ensure_ascii=False),
            request,
            budget,
            input_tokens=input_tokens,
            model="mock",
        )
