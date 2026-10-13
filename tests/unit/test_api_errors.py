"""Stable HTTP status / envelope mapping for API-RKG-CORE-v1 (NFR-SEC / AC-058)."""

from __future__ import annotations

from rkg.api.errors import error_body, error_response, http_status
from rkg.ingestion import SourceError
from rkg.jobs import IndexJobBusyError
from rkg.storage.errors import RepositoryConflictError


def test_stable_error_codes_map_to_contract_status() -> None:
    assert http_status("unauthorized") == 401
    assert http_status("not_found") == 404
    assert http_status("snapshot_unavailable") == 410
    assert http_status("invalid_budget") == 422
    assert http_status("llm_disabled") == 503
    assert http_status("llm_timeout") == 504
    assert http_status("llm_malformed_response") == 502
    assert http_status("index_job_busy", IndexJobBusyError()) == 409
    assert http_status("repository_conflict", RepositoryConflictError()) == 409
    assert (
        http_status(
            "source_outside_allowed_roots",
            SourceError("source_outside_allowed_roots"),
        )
        == 422
    )
    assert http_status("source_link_escape", SourceError("source_link_escape")) == 422
    assert (
        http_status("file_limit_exceeded", SourceError("file_limit_exceeded")) == 422
    )
    assert http_status("source_not_found") == 422
    assert http_status("unexpected_failure") == 500


def test_error_envelope_exposes_code_only_without_host_path() -> None:
    body = error_body("source_outside_allowed_roots")
    assert body == {
        "error": {
            "code": "source_outside_allowed_roots",
            "message": "source outside allowed roots",
        }
    }
    rendered = str(body)
    assert "C:\\" not in rendered
    assert "/Users/" not in rendered
    assert "E:" not in rendered

    response = error_response("unauthorized")
    assert response.status_code == 401
    assert response.body
    assert b"unauthorized" in response.body
    assert b"token" not in response.body
