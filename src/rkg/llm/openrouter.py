"""OpenRouter JSON-schema adapter. Errors expose codes, never response bodies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rkg.llm.chat_completions import ChatCompletionsProvider, Transport
from rkg.llm.http import post_json
from rkg.llm.provider import StructuredRequest

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


def _post(
    payload: Mapping[str, Any], headers: Mapping[str, str], timeout: float | None
) -> Mapping[str, Any]:
    return post_json(ENDPOINT, payload, headers, timeout)


class OpenRouterProvider(ChatCompletionsProvider):
    key_env = "OPENROUTER_API_KEY"
    model_env = "OPENROUTER_MODEL"
    default_model = MODEL

    def __init__(self, transport: Transport = _post) -> None:
        super().__init__(transport)

    def payload(self, request: StructuredRequest, model: str) -> dict[str, Any]:
        payload = super().payload(request, model)
        payload.update(provider={"require_parameters": True}, usage={"include": True})
        return payload
