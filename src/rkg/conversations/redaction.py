"""Redact conversation text before it is stored.

Glossary: drop credentials, secret/config values, raw source, provider
chain-of-thought and untrusted markup. Remaining prose is the allowlist.
The replacement token is stable so a second pass does not grow the text.
"""

from __future__ import annotations

import re

REDACTED = "[redacted]"

_THINK = re.compile(r"(?is)<think>.*?(?:</think>|$)")
_COT = re.compile(r"(?is)\bchain[-_ ]of[-_ ]thought\b\s*:.*?(?:\n\s*\n|$)")
_PEM = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_FENCE = re.compile(r"```.*?```", re.DOTALL)
_CODE_BLOCK = re.compile(r"(?is)<(script|style|pre|code)\b[^>]*>.*?(?:</\1>|$)")
_SECRET_ASSIGN = re.compile(
    r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?key|"
    r"client[_-]?secret|token|credential|authorization)\b"
    r"\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|\S+)"
)
_ENV_SECRET = re.compile(
    r"\b[A-Z][A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN|CREDENTIAL|API_KEY)[A-Z0-9_]*"
    r"\s*=\s*\S+"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-+/=]{8,}")
_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_WIN_PATH = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"'`<>|]+")
_POSIX_PATH = re.compile(
    r"(?:/(?:home|Users|usr|var|etc|tmp|opt|private)/[^\s\"'`<>]+)"
)
_JS_URL = re.compile(r"(?i)\bjavascript:\S+")
_TAG = re.compile(r"<[^>]+>")

_DROP_KEYS = frozenset(
    {
        "chain_of_thought",
        "reasoning",
        "cot",
        "raw_source",
        "raw_value",
        "value",
        "password",
        "secret",
        "token",
        "credential",
        "api_key",
        "authorization",
    }
)


def redact_conversation_text(text: str) -> str:
    """Return prose with forbidden fragments replaced by ``[redacted]``."""
    cleaned = text
    for pattern in (
        _THINK,
        _COT,
        _PEM,
        _FENCE,
        _CODE_BLOCK,
        _SECRET_ASSIGN,
        _ENV_SECRET,
        _BEARER,
        _AWS,
        _WIN_PATH,
        _POSIX_PATH,
        _JS_URL,
    ):
        cleaned = pattern.sub(REDACTED, cleaned)
    cleaned = _TAG.sub("", cleaned)
    return cleaned


def redact_json_value(value: object) -> object:
    """Redact nested strings and drop keys that are secret or reasoning."""
    if isinstance(value, str):
        return redact_conversation_text(value)
    if isinstance(value, list):
        return [redact_json_value(item) for item in value]
    if isinstance(value, dict):
        kept: dict[str, object] = {}
        for key, item in value.items():
            if str(key).casefold() in _DROP_KEYS:
                continue
            kept[str(key)] = redact_json_value(item)
        return kept
    return value
