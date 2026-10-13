"""Shared completion lifecycle; adapters own keys, wire profile and endpoint."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import Any

from rkg.llm.provider import (
    LLMError,
    StructuredRequest,
    StructuredResponse,
    TurnBudget,
    parse_response,
    prepare_call,
)
from rkg.terminal_logging import log_debug

Transport = Callable[
    [Mapping[str, Any], Mapping[str, str], float | None], Mapping[str, Any]
]


class ChatCompletionsProvider:
    key_env: str
    model_env: str
    default_model: str

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @property
    def enabled(self) -> bool:
        """Nonsecret local availability, with no network/model request."""
        return bool(os.environ.get(self.key_env, "").strip())

    def complete(
        self, request: StructuredRequest, budget: TurnBudget
    ) -> StructuredResponse:
        key = os.environ.get(self.key_env, "").strip()
        if not key:
            raise LLMError("llm_disabled")
        model = (
            os.environ.get(self.model_env, self.default_model).strip()
            or self.default_model
        )
        if len(model) > 200 or any(character.isspace() for character in model):
            raise LLMError("llm_invalid_request")
        input_tokens, timeout = prepare_call(request, budget)
        payload = self.payload(request, model)
        if request.max_output_tokens is not None:
            payload["max_completion_tokens"] = request.max_output_tokens
        log_debug(
            "provider_request",
            provider=self.key_env.removesuffix("_API_KEY").lower(),
            payload=payload,
            timeout_seconds=timeout,
        )
        try:
            data = self._transport(
                payload,
                {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                timeout,
            )
        except LLMError:
            raise
        except TimeoutError:
            raise LLMError("llm_timeout") from None
        except Exception:
            raise LLMError("llm_provider_error") from None
        log_debug("provider_response", response=data)
        budget.remaining_seconds()
        try:
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise LLMError("llm_budget_exceeded")
            if choice.get("finish_reason") != "stop":
                raise LLMError("llm_malformed_response", reason="finish_reason")
            message = choice["message"]
            if message.get("refusal"):
                raise LLMError("llm_malformed_response", reason="refusal")
            content = message["content"]
        except (KeyError, IndexError, TypeError, AttributeError):
            raise LLMError("llm_malformed_response", reason="response_shape") from None
        return parse_response(
            content,
            request,
            budget,
            input_tokens=input_tokens,
            model=model,
            usage=data.get("usage"),
        )

    def schema_for_wire(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        return dict(schema)

    def payload(self, request: StructuredRequest, model: str) -> dict[str, Any]:
        return {
            "model": model,
            "messages": [dict(item) for item in request.messages],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema_name,
                    "strict": True,
                    "schema": self.schema_for_wire(request.schema),
                },
            },
            "stream": False,
        }
