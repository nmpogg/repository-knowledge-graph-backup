"""Bounded JSON transport for fixed provider endpoints; only safe error codes escape."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any

from rkg.llm.provider import LLMError
from rkg.terminal_logging import debug_enabled, log_debug


class _RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Keep credentials and requests on the adapter's fixed endpoint.
        return None


def post_json(
    endpoint: str,
    payload: Mapping[str, Any],
    headers: Mapping[str, str],
    timeout: float | None,
) -> Mapping[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )
    try:
        opener = urllib.request.build_opener(_RejectRedirect())
        with opener.open(request, timeout=timeout) as response:
            # Reject unexpectedly large responses before parsing them.
            raw = response.read(1_000_001)
            log_debug(
                "provider_http_response",
                status=getattr(response, "status", None),
                body=raw.decode("utf-8", errors="backslashreplace"),
                bytes_read=len(raw),
            )
    except TimeoutError:
        raise LLMError("llm_timeout") from None
    except urllib.error.HTTPError as exc:
        # Body detail is restricted to explicit terminal DEBUG.
        if debug_enabled():
            try:
                body = exc.read(1_000_001).decode("utf-8", errors="backslashreplace")
                log_debug("provider_http_error", status=exc.code, body=body)
            except Exception as read_error:
                log_debug(
                    "provider_http_error",
                    status=exc.code,
                    body_read_error=type(read_error).__name__,
                )
        # Keep safe public error mapping.
        if exc.code in {408, 504}:
            raise LLMError("llm_timeout") from None
        raise LLMError("llm_provider_error") from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise LLMError("llm_timeout") from None
        raise LLMError("llm_provider_error") from None
    except OSError:
        raise LLMError("llm_provider_error") from None
    if len(raw) > 1_000_000:
        raise LLMError("llm_malformed_response", reason="response_size")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, ValueError):
        raise LLMError("llm_malformed_response", reason="invalid_json") from None
    if not isinstance(value, dict):
        raise LLMError("llm_malformed_response", reason="response_shape")
    return value
