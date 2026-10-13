"""Application console logs; explicit DEBUG enables model/validator detail."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_LOGGER = logging.getLogger("rkg.conversation")
_CONTEXT: ContextVar[dict[str, str]] = ContextVar("rkg_log_context", default={})


class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if not getattr(record, "rkg_context_emitted", False):
            text += " " + " ".join(
                f"{key}={value}" for key, value in _CONTEXT.get().items()
            )
        return text


def configure_terminal_logging(level: str = "info") -> None:
    numeric = {"info": logging.INFO, "debug": logging.DEBUG}[level]
    _LOGGER.setLevel(numeric)
    _LOGGER.disabled = False
    _LOGGER.propagate = False
    handlers = [h for h in _LOGGER.handlers if getattr(h, "_rkg_terminal", False)]
    if not handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler._rkg_terminal = True
        handler.setFormatter(_ConsoleFormatter("%(asctime)s %(levelname)s %(message)s"))
        _LOGGER.addHandler(handler)
        handlers = [handler]
    for handler in handlers:
        handler.setLevel(numeric)


def current_context() -> dict[str, str]:
    return dict(_CONTEXT.get())


@contextmanager
def log_context(**fields: str) -> Iterator[None]:
    token = _CONTEXT.set({**_CONTEXT.get(), **fields})
    try:
        yield
    finally:
        _CONTEXT.reset(token)


def _emit(level: int, event: str, fields: dict[str, Any]) -> None:
    if not _LOGGER.isEnabledFor(level):
        return
    context = " ".join(f"{name}={value}" for name, value in _CONTEXT.get().items())
    try:
        detail = json.dumps(fields, ensure_ascii=False, allow_nan=False, default=str)
    except Exception:
        detail = '{"diagnostic":"unserializable_payload"}'
    _LOGGER.log(
        level,
        "event=%s %s detail=%s",
        event,
        context,
        detail,
        extra={"rkg_context_emitted": True},
    )


def log_event(event: str, **fields: Any) -> None:
    _emit(logging.INFO, event, fields)


def log_debug(event: str, **fields: Any) -> None:
    _emit(logging.DEBUG, event, fields)


def debug_enabled() -> bool:
    return _LOGGER.isEnabledFor(logging.DEBUG)


def log_debug_exception(event: str, exception: BaseException) -> None:
    if not debug_enabled():
        return
    try:
        message = str(exception)
    except Exception:
        message = "<exception_message_unavailable>"
    log_debug(event, exception_type=type(exception).__name__, message=message)
