"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-vue-router.

Vue + TypeScript language facts merge before the Vue Router deep adapter.
Every scored entity and edge is listed (allow_unlisted_actual is false).
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
    run_polyglot_pipeline,
)

EXPECTED = Path(__file__).with_name("expected_vue_router.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-vue-router"
_VUE_PATTERNS = ("*.vue", "**/*.vue")
_TS_PATTERNS = ("*.ts", "**/*.ts", "*.tsx", "**/*.tsx", "package.json")
_IGNORE = ("**/node_modules/**", "**/dist/**", "**/coverage/**")


def _vue_adapter():
    from rkg.adapters.vue_language import VueLanguageAdapter

    return VueLanguageAdapter()


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _router_adapter():
    from rkg.adapters.vue_router_framework import VueRouterFrameworkAdapter

    return VueRouterFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-vue-router"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    paths = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert paths == {
        "/",
        "/orders",
        "/orders/:orderId",
        "/admin",
        "/admin/users",
        "/legacy",
    }
    navigate = {
        (item["source"], item["target"])
        for item in payload["edges"]
        if item.get("type") == "calls"
        and item.get("rule_id") == "RKG.vue_router.navigate.v1"
    }
    assert navigate == {
        ("src.navigation.openOrders.openOrders", "src.views.Orders.setup"),
        ("src.navigation.openOrders.openUsers", "src.views.Users.setup"),
        ("src.router.legacy.openLegacy", "src.views.Legacy.setup"),
    }


def test_vue_router_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_polyglot_pipeline(
        repository_id="rkg-fixture-vue-router",
        root=root,
        language_specs=(
            (_vue_adapter, _VUE_PATTERNS),
            (_typescript_adapter, _TS_PATTERNS),
        ),
        ignore_patterns=_IGNORE,
        deep_factories=(_router_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
