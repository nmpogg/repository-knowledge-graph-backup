"""Deterministic turn identity from the business key."""

from __future__ import annotations

import hashlib

from rkg.storage._util import dumps_json


def deterministic_turn_id(conversation_id: str, client_request_id: str) -> str:
    """``turn_`` + full lowercase SHA-256 of ``conversation_id:client_request_id``."""
    material = f"{conversation_id}:{client_request_id}".encode()
    return "turn_" + hashlib.sha256(material).hexdigest()


def request_fingerprint(
    question: str, root_id: str | None, *, ui_locale: str | None = None
) -> str:
    """Hash the client body so redaction does not change idempotency."""
    body = {"question": question, "root_id": root_id}
    if ui_locale == "en":
        body["ui_locale"] = "en"
    payload = dumps_json(body)
    return hashlib.sha256(payload.encode()).hexdigest()
