"""Loopback session gate for mutations. Reads stay snapshot-scoped."""

from __future__ import annotations

import hmac
from urllib.parse import urlsplit

_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def _host_name(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(f"//{value}" if "//" not in value else value)
    name = parsed.hostname
    return name.casefold() if name else None


def _origin_name(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return parsed.hostname.casefold()


def mutation_allowed(headers: object, session_token: str) -> bool:
    """True when Host, optional Origin, and X-RKG-Session are local and valid."""
    host = _host_name(_header(headers, "host"))
    if host not in _LOOPBACK:
        return False
    origin = _origin_name(_header(headers, "origin"))
    if origin is not None and origin not in _LOOPBACK:
        return False
    supplied = _header(headers, "x-rkg-session")
    if not session_token or not supplied:
        return False
    return hmac.compare_digest(supplied.encode("utf-8"), session_token.encode("utf-8"))


def _header(headers: object, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter(name)
    if value is None:
        return None
    text = str(value)
    return text if text else None
