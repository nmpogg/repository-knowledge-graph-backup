"""HTTP envelope for API-RKG-CORE-v1. Messages stay free of host paths."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from rkg.ingestion import SourceError
from rkg.jobs import IndexJobBusyError
from rkg.storage.errors import ConflictError

_STATUS = {
    "unauthorized": 401,
    "not_found": 404,
    "snapshot_unavailable": 410,
    "invalid_budget": 422,
    "invalid_request": 422,
    "invalid_turn_request": 422,
    "repository_source_immutable": 422,
    "llm_disabled": 503,
    "llm_timeout": 504,
    "llm_provider_error": 502,
    "llm_malformed_response": 502,
    "llm_budget_exceeded": 502,
    "llm_invalid_request": 502,
    "provider_failed": 502,
    "invalid_provider_status": 502,
}


def http_status(code: str, error: Exception | None = None) -> int:
    if code in _STATUS:
        return _STATUS[code]
    if isinstance(error, SourceError):
        return 422
    if isinstance(error, IndexJobBusyError):
        return 409
    if isinstance(error, ConflictError):
        return 409
    if code.endswith("_invalid") or code.startswith("source_"):
        return 422
    return 500


def error_body(code: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": code.replace("_", " ")}}


def error_response(code: str, error: Exception | None = None) -> JSONResponse:
    return JSONResponse(status_code=http_status(code, error), content=error_body(code))
