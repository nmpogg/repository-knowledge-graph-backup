"""OBS-RKG-001 census for tests/evaluation/fixtures/rkg-fixture-django.

Oracle: README Expected inventory + Intentional negative cases.
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

EXPECTED = Path(__file__).with_name("expected_django.json")
FIXTURE = "tests/evaluation/fixtures/rkg-fixture-django"
_PY_PATTERNS = ("*.py", "**/*.py")


def _python_adapter():
    from rkg.adapters.python_language import PythonLanguageAdapter

    return PythonLanguageAdapter()


def _django_adapter():
    from rkg.adapters.django_framework import DjangoFrameworkAdapter

    return DjangoFrameworkAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-django"
    assert payload["match_policy"]["allow_unlisted_actual"] is False
    paths = {
        item["required_attributes"]["path"]
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert paths == {
        "/bare/",
        "/health/",
        "/orders/<int:pk>/",
        "/shop/orders/",
        "/shop/varied/",
        "^legacy/$",
        "^old/$",
    }
    methods = {
        item["required_attributes"].get("method")
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert methods == {None, "GET", "POST"}


def test_django_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-django",
        root=root,
        include_patterns=_PY_PATTERNS,
        ignore_patterns=("**/__pycache__/**",),
        language_factory=_python_adapter,
        deep_factories=(_django_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
