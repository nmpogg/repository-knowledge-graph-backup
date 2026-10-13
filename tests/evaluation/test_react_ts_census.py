"""OBS-RKG-001 census for repo-test/rkg-fixture-react-ts.

Oracle: README Expected inventory + Intentional negative cases.
Future adapters imported lazily; missing modules → valid RED.
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

EXPECTED = Path(__file__).with_name("expected_react_ts.json")
FIXTURE = "repo-test/rkg-fixture-react-ts"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _react_router_adapter():
    from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter

    return ReactRouterFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-react-ts"
    assert payload["entities"]
    assert payload["edges"]
    nav = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if item.get("type") == "navigation_route"
        or item.get("semantic_kind") == "navigation_route"
    }
    assert nav == {
        "/",
        "/orders",
        "/orders/:orderId",
        "/orders/:orderId/edit",
        "/admin/users",
        "*",
    }


def test_react_ts_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-react-ts",
        root=root,
        include_patterns=_TS_PATTERNS,
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        language_factory=_typescript_adapter,
        deep_factories=(_react_router_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
