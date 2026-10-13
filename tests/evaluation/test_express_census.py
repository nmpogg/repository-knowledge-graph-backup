"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-express."""

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

EXPECTED = Path(__file__).with_name("expected_express.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-express"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _express_adapter():
    from rkg.adapters.express_framework import ExpressFrameworkAdapter

    return ExpressFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-express"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    paths = {
        (
            item["required_attributes"]["method"],
            item["required_attributes"]["path"],
        )
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert paths == {
        ("GET", "/health"),
        ("GET", "/orders"),
        ("POST", "/orders"),
        ("DELETE", "/orders/:id"),
        ("PUT", "/orders/:id"),
    }


def test_express_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-express",
        root=root,
        include_patterns=_TS_PATTERNS,
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        language_factory=_typescript_adapter,
        deep_factories=(_express_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
