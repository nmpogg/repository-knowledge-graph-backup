"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-tanstack-router.

Oracle lists every scored entity and edge. allow_unlisted_actual is false.
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

EXPECTED = Path(__file__).with_name("expected_tanstack_router.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-tanstack-router"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _tanstack_router_adapter():
    from rkg.adapters.tanstack_router_framework import TanStackRouterFrameworkAdapter

    return TanStackRouterFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-tanstack-router"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    assert payload["entities"]
    assert payload["edges"]
    nav = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if item.get("type") == "navigation_route"
        or item.get("semantic_kind") == "navigation_route"
        or (item.get("required_attributes") or {}).get("kind") == "navigation"
    }
    calls = {
        (item["source"], item["target"])
        for item in payload["edges"]
        if item.get("type") == "calls"
        and item.get("rule_id") == "RKG.tanstack_router.navigate.v1"
    }
    assert nav == {"/", "/orders", "/orders/$orderId", "/catalog"}
    assert ("src.go.openOrders", "src.pages.OrdersPage") in calls
    assert ("src.go.openOrders", "src.pages.OrderDetailPage") in calls


def test_tanstack_router_census_matches_expected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-tanstack-router",
        root=root,
        include_patterns=_TS_PATTERNS,
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        language_factory=_typescript_adapter,
        deep_factories=(_tanstack_router_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
