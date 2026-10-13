"""OBS-RKG-001 census for repo-test/rkg-fixture-nuxt4.

Oracle: README UI routes, Nitro HTTP endpoints, symbols, config, negatives.
Vue + TypeScript language facts merge before Nuxt framework extract.
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

EXPECTED = Path(__file__).with_name("expected_nuxt.json")
FIXTURE = "repo-test/rkg-fixture-nuxt4"
_VUE_PATTERNS = ("*.vue", "**/*.vue")
_TS_PATTERNS = ("*.ts", "**/*.ts", "*.tsx", "**/*.tsx", "package.json", "tsconfig*.json")
_IGNORE = (
    "**/.nuxt/**",
    "**/.output/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/coverage/**",
)


def _vue_adapter():
    from rkg.adapters.vue_language import VueLanguageAdapter

    return VueLanguageAdapter()


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _nuxt_adapter():
    from rkg.adapters.nuxt_framework import NuxtFrameworkAdapter

    return NuxtFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-nuxt4"
    assert payload["entities"]
    assert payload["edges"]
    ui_paths = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if item.get("semantic_kind") == "navigation_route"
        or item.get("type") == "navigation_route"
    }
    assert ui_paths == {"/", "/orders", "/orders/:orderId", "/account/profile"}
    http = {
        (
            item["required_attributes"]["method"],
            item["required_attributes"]["path"],
        )
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert http == {
        ("GET", "/api/orders"),
        ("GET", "/api/orders/:orderId"),
        ("POST", "/api/orders/:orderId/cancel"),
    }


def test_nuxt_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_polyglot_pipeline(
        repository_id="rkg-fixture-nuxt4",
        root=root,
        language_specs=(
            (_vue_adapter, _VUE_PATTERNS),
            (_typescript_adapter, _TS_PATTERNS),
        ),
        ignore_patterns=_IGNORE,
        deep_factories=(_nuxt_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
