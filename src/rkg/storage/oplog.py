"""Operational log lines for conversation turns.

Identifiers and status codes only. Question, answer, chain-of-thought and
request bodies are never written here.
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger("rkg.conversation")
_FIELDS = ("conversation_id", "turn_id", "status", "error_code")


def log_operation(event: str, **fields: object) -> None:
    """Log one fixed event. ``event`` must be a code, not user text."""
    parts = [f"event={event}"]
    for key in _FIELDS:
        value = fields.get(key)
        if value is None:
            continue
        parts.append(f"{key}={value}")
    revision = fields.get("revision")
    if isinstance(revision, int):
        parts.append(f"revision={revision}")
    _LOGGER.info(" ".join(parts))
