"""Static rejection codes only: never log model/request/exception text."""

import logging

SAFE_REASONS = frozenset(
    {
        "invalid_content",
        "invalid_json",
        "invalid_schema",
        "invalid_response",
        "response_shape",
        "response_size",
        "refusal",
        "finish_reason",
        "invalid_plan",
        "invalid_graph_references",
        "provider_failure",
    }
)
_STAGES = frozenset({"read_plan", "narrative", "narrative_grounding", "unknown"})
_CODES = frozenset(
    {
        "llm_disabled",
        "llm_timeout",
        "llm_budget_exceeded",
        "llm_malformed_response",
        "llm_provider_error",
        "llm_invalid_request",
        "provider_failed",
    }
)
_LOGGER = logging.getLogger("rkg.conversation")


def log_rejection(stage: object, reason: object, code: object) -> None:
    stage = stage if isinstance(stage, str) and stage in _STAGES else "unknown"
    reason = (
        reason
        if isinstance(reason, str) and reason in SAFE_REASONS
        else "invalid_response"
    )
    code = code if isinstance(code, str) and code in _CODES else "provider_failed"
    _LOGGER.warning(
        "event=llm_rejected stage=%s reason=%s error_code=%s", stage, reason, code
    )
