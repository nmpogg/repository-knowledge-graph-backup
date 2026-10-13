"""Direct OpenAI strict Structured Outputs with authoritative local validation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from rkg.llm.chat_completions import ChatCompletionsProvider, Transport
from rkg.llm.http import post_json
from rkg.llm.provider import StructuredRequest

ENDPOINT = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"


def _post(
    payload: Mapping[str, Any], headers: Mapping[str, str], timeout: float | None
) -> Mapping[str, Any]:
    return post_json(ENDPOINT, payload, headers, timeout)


def wire_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Project schema nodes, never property names. Local schema retains uniqueness.

    Artifact annotations, uniqueness and string lengths are locally enforced.
    The original request remains unchanged for parse_response and graph guards.
    """
    result = deepcopy(dict(schema))

    def project(node: dict[str, Any]) -> None:
        for keyword in (
            "$schema",
            "$id",
            "x-aide",
            "uniqueItems",
            "minLength",
            "maxLength",
        ):
            node.pop(keyword, None)
        enum = node.get("enum")
        if (
            "type" not in node
            and isinstance(enum, list)
            and enum
            and all(isinstance(item, str) for item in enum)
        ):
            node["type"] = "string"
        for keyword in ("properties", "$defs"):
            for child in node.get(keyword, {}).values():
                if isinstance(child, dict):
                    project(child)
        if isinstance(node.get("items"), dict):
            project(node["items"])
        for child in node.get("anyOf", []):
            if isinstance(child, dict):
                project(child)

    project(result)
    return result


class OpenAIProvider(ChatCompletionsProvider):
    key_env = "OPENAI_API_KEY"
    model_env = "OPENAI_MODEL"
    default_model = MODEL

    def __init__(self, transport: Transport = _post) -> None:
        super().__init__(transport)

    def schema_for_wire(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        return wire_schema(schema)

    def payload(self, request: StructuredRequest, model: str) -> dict[str, Any]:
        payload = super().payload(request, model)
        payload["store"] = False
        return payload
