"""Structured LLM contract and per-turn resource limits.

Callers own retrieval and validate graph citations. Providers receive only bounded
messages and a JSON schema; they never receive storage or tool handles.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import jsonschema
import tiktoken
from tiktoken.load import load_tiktoken_bpe

from rkg.llm.diagnostics import SAFE_REASONS
from rkg.terminal_logging import log_debug

_PATTERN = "|".join(
    [
        r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
        r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?""",
        r"""\p{N}{1,3}""",
        r""" ?[^\s\p{L}\p{N}]+[\r\n/]*""",
        r"""\s*[\r\n]+""",
        r"""\s+(?!\S)""",
        r"""\s+""",
    ]
)
_ENCODING = tiktoken.Encoding(
    name="o200k_base",
    pat_str=_PATTERN,
    mergeable_ranks=load_tiktoken_bpe(
        str(Path(__file__).parent / "data" / "o200k_base.tiktoken"),
        expected_hash="446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d",
    ),
    special_tokens={"<|endoftext|>": 199999, "<|endofprompt|>": 200018},
)


class LLMError(Exception):
    """Safe, stable error for transport and API mapping."""

    def __init__(self, code: str, *, reason: str | None = None) -> None:
        self.reason = (
            reason if isinstance(reason, str) and reason in SAFE_REASONS else None
        )
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class TurnBudget:
    """Shared across all provider calls and graph operations in one turn."""

    max_model_calls: int | None = None
    max_graph_queries: int | None = None
    max_output_tokens: int | None = None
    timeout_seconds: float | None = None
    model_calls: int = 0
    graph_queries: int = 0
    started_at: float = field(default_factory=time.monotonic)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    def __post_init__(self) -> None:
        if self.max_model_calls is not None and self.max_model_calls < 1:
            raise ValueError("invalid model-call budget")
        if self.max_graph_queries is not None and self.max_graph_queries < 0:
            raise ValueError("invalid graph-query budget")
        if self.max_output_tokens is not None and self.max_output_tokens < 1:
            raise ValueError("invalid output-token budget")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("invalid timeout budget")

    def remaining_seconds(self) -> float | None:
        if self.timeout_seconds is None:
            return None
        remaining = self.timeout_seconds - (self.clock() - self.started_at)
        if remaining <= 0:
            raise LLMError("llm_timeout")
        return remaining

    def reserve_model_call(self) -> float | None:
        remaining = self.remaining_seconds()
        if (
            self.max_model_calls is not None
            and self.model_calls >= self.max_model_calls
        ):
            raise LLMError("llm_budget_exceeded")
        self.model_calls += 1
        return remaining

    def reserve_graph_query(self) -> None:
        self.remaining_seconds()
        if (
            self.max_graph_queries is not None
            and self.graph_queries >= self.max_graph_queries
        ):
            raise LLMError("llm_budget_exceeded")
        self.graph_queries += 1


@dataclass(frozen=True, slots=True)
class StructuredRequest:
    messages: tuple[Mapping[str, str], ...]
    schema_name: str
    schema: Mapping[str, Any]
    max_output_tokens: int | None = None
    max_input_tokens: int | None = None

    def __post_init__(self) -> None:
        if not self.messages or not self.schema_name or len(self.schema_name) > 64:
            raise LLMError("llm_invalid_request")
        if any(
            limit is not None and limit < 1
            for limit in (self.max_output_tokens, self.max_input_tokens)
        ):
            raise LLMError("llm_invalid_request")
        if any(
            set(message) != {"role", "content"}
            or message["role"] not in {"system", "user", "assistant"}
            or not isinstance(message["content"], str)
            for message in self.messages
        ):
            raise LLMError("llm_invalid_request")
        try:
            jsonschema.Draft202012Validator.check_schema(dict(self.schema))
        except jsonschema.SchemaError:
            raise LLMError("llm_invalid_request") from None


@dataclass(frozen=True, slots=True)
class StructuredResponse:
    value: dict[str, Any]
    input_tokens: int
    output_tokens: int
    model: str
    cost: float | None = None


class StructuredProvider(Protocol):
    def complete(
        self, request: StructuredRequest, budget: TurnBudget
    ) -> StructuredResponse: ...


def count_tokens(messages: Sequence[Mapping[str, str]]) -> int:
    """Conservative local preflight; wire framing is accounted for per message."""
    return 3 + sum(
        4
        + len(_ENCODING.encode(message["role"]))
        + len(_ENCODING.encode(message["content"]))
        for message in messages
    )


def prepare_call(
    request: StructuredRequest, budget: TurnBudget
) -> tuple[int, float | None]:
    if budget.max_output_tokens is not None and (
        request.max_output_tokens is None
        or request.max_output_tokens > budget.max_output_tokens
    ):
        raise LLMError("llm_budget_exceeded")
    input_tokens = count_tokens(request.messages)
    # Schema travels with the request and uses model context too.
    schema_text = json.dumps(request.schema, ensure_ascii=False)
    input_tokens += len(_ENCODING.encode(schema_text))
    if request.max_input_tokens is not None and input_tokens > request.max_input_tokens:
        raise LLMError("llm_budget_exceeded")
    return input_tokens, budget.reserve_model_call()


def parse_response(
    content: object,
    request: StructuredRequest,
    budget: TurnBudget,
    *,
    input_tokens: int,
    model: str,
    usage: object = None,
) -> StructuredResponse:
    budget.remaining_seconds()
    if not isinstance(content, str):
        raise LLMError("llm_malformed_response", reason="invalid_content")
    actual_output = len(_ENCODING.encode(content))
    if (
        request.max_output_tokens is not None
        and actual_output > request.max_output_tokens
    ):
        raise LLMError("llm_budget_exceeded")
    try:
        value = json.loads(content)
    except ValueError as exc:
        log_debug("json_validation_failed", message=str(exc), content=content)
        raise LLMError("llm_malformed_response", reason="invalid_json") from None
    try:
        jsonschema.validate(value, request.schema)
    except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        log_debug(
            "schema_validation_failed",
            validator=exc.validator,
            instance_path=list(exc.absolute_path),
            schema_path=list(exc.absolute_schema_path),
            message=exc.message,
        )
        raise LLMError("llm_malformed_response", reason="invalid_schema") from None
    if not isinstance(value, dict):
        raise LLMError("llm_malformed_response", reason="invalid_schema")
    reported_input = _token_usage(usage, "prompt_tokens")
    reported_output = _token_usage(usage, "completion_tokens")
    if (
        request.max_output_tokens is not None
        and reported_output is not None
        and reported_output > request.max_output_tokens
    ):
        raise LLMError("llm_budget_exceeded")
    cost = usage.get("cost") if isinstance(usage, dict) else None
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0:
        cost = None
    return StructuredResponse(
        value=value,
        input_tokens=reported_input if reported_input is not None else input_tokens,
        output_tokens=reported_output if reported_output is not None else actual_output,
        model=model,
        cost=float(cost) if cost is not None else None,
    )


def _token_usage(usage: object, key: str) -> int | None:
    value = usage.get(key) if isinstance(usage, dict) else None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
