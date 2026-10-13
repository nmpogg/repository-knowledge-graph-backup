"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-next.

Oracle lists every scored fact. Dynamic segments use colon spelling
([orderId] → :orderId).
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

EXPECTED = Path(__file__).with_name("expected_next.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-next"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _next_adapter():
    from rkg.adapters.next_framework import NextFrameworkAdapter

    return NextFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-next"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    nav = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if (item.get("required_attributes") or {}).get("kind") == "navigation"
    }
    assert nav == {
        "/",
        "/orders",
        "/orders/:orderId",
        "/catalog",
        "/account",
        "/about",
        "/legacy",
        "/blog/:slug",
    }
    http = {
        (
            item["required_attributes"]["method"],
            item["required_attributes"]["path"],
        )
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
        and (item.get("required_attributes") or {}).get("method")
    }
    assert http == {
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/:orderId"),
        ("GET", "/api/health"),
    }
    calls = [
        item
        for item in payload["edges"]
        if item["type"] == "calls" and item["rule_id"] == "RKG.next.navigation.v1"
    ]
    handled = [
        item
        for item in payload["edges"]
        if item["type"] == "handled_by" and item["rule_id"] == "RKG.next.handler.v1"
    ]
    assert len(calls) == 4
    assert len(handled) == 12
    assert not any(item["type"] == "depends_on" for item in payload["edges"])


def test_next_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-next",
        root=root,
        include_patterns=_TS_PATTERNS,
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        language_factory=_typescript_adapter,
        deep_factories=(_next_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
