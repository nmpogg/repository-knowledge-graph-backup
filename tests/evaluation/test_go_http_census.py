"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-go-http.

Pipeline: Go language adapter plus rkg.go-http. The event-worker fixture has
no Gin, chi, or gorilla/mux routes, so this adapter must leave it unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.evaluation.census_support import (
    SECRET,
    compare_census,
    fixture_root,
    format_report,
    load_expected,
    run_language_pipeline,
)

EXPECTED = Path(__file__).with_name("expected_go_http.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-go-http"
WORKER = "repo-test/rkg-fixture-go-event-worker"
_GO_PATTERNS = ("*.go", "**/*.go")
_IGNORE = ("**/testdata/**", "**/*_test.go")


def _go_adapter():
    from rkg.adapters.go_language import GoLanguageAdapter

    return GoLanguageAdapter()


def _go_http_adapter():
    from rkg.adapters.go_http_framework import GoHTTPFrameworkAdapter

    return GoHTTPFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-go-http"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    paths = {
        (item["required_attributes"]["method"], item["required_attributes"]["path"])
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert paths == {("GET", "/health"), ("GET", "/orders"), ("POST", "/shipments")}
    assert not any(item.get("type") == "Namespace" for item in payload["entities"])


def test_go_http_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-go-http",
        root=root,
        include_patterns=_GO_PATTERNS,
        ignore_patterns=_IGNORE,
        language_factory=_go_adapter,
        deep_factories=(_go_http_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0


def test_event_worker_facts_are_unchanged() -> None:
    root = fixture_root(WORKER)
    shared = {
        "root": root,
        "include_patterns": _GO_PATTERNS,
        "ignore_patterns": ("**/testdata/**",),
        "language_factory": _go_adapter,
    }
    base = run_language_pipeline(repository_id="rkg-fixture-go-event-worker", **shared)
    with_http = run_language_pipeline(
        repository_id="rkg-fixture-go-event-worker",
        deep_factories=(_go_http_adapter,),
        **shared,
    )
    assert base == with_http
