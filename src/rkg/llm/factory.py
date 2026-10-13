"""Explicit server provider selection; no credential probing or automatic fallback."""

import os

from rkg.llm.openai import OpenAIProvider
from rkg.llm.openrouter import OpenRouterProvider
from rkg.llm.provider import LLMError


def configured_provider() -> OpenAIProvider | OpenRouterProvider:
    name = os.environ.get("RKG_LLM_PROVIDER", "openrouter").strip().lower()
    if name == "openrouter":
        return OpenRouterProvider()
    if name == "openai":
        return OpenAIProvider()
    raise LLMError("llm_invalid_request")
