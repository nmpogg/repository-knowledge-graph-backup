"""OBS-RKG-001 census for repo-test/soopi (Python FastAPI pilot).

Oracle: API-SOOPI-001 routes, CMP layering, SQLAlchemy models/settings.
Uses production deep-supported adapters (python / fastapi / sqlalchemy).
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

EXPECTED = Path(__file__).with_name("expected_soopi.json")
FIXTURE = "repo-test/soopi"
_PY_PATTERNS = ("*.py", "**/*.py")
_IGNORE = (
    "**/.venv/**",
    "**/__pycache__/**",
    "**/.cache/**",
    "**/tests/**",
    "**/alembic/**",
    "**/.pytest_cache/**",
)


def _python_adapter():
    from rkg.adapters.python_language import PythonLanguageAdapter

    return PythonLanguageAdapter()


def _fastapi_adapter():
    from rkg.adapters.fastapi_framework import FastAPIFrameworkAdapter

    return FastAPIFrameworkAdapter()


def _sqlalchemy_adapter():
    from rkg.adapters.sqlalchemy_data import SQLAlchemyDataAccessAdapter

    return SQLAlchemyDataAccessAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "soopi"
    assert payload["entities"]
    assert payload["edges"]
    assert payload.get("match_policy", {}).get("allow_unlisted_actual") is True
    endpoints = {
        (
            item["required_attributes"]["method"],
            item["required_attributes"]["path"],
        )
        for item in payload["entities"]
        if item.get("type") == "Endpoint"
    }
    assert ("POST", "/api/v1/orders") in endpoints
    assert ("POST", "/api/v1/auth/login") in endpoints
    assert ("GET", "/api/v1/orders/webhooks/vnpay") in endpoints
    tables = {
        item["required_attributes"]["table"]
        for item in payload["entities"]
        if item.get("type") == "DataResource"
    }
    assert tables == {
        "users",
        "addresses",
        "refresh_sessions",
        "categories",
        "products",
        "product_variants",
        "carts",
        "cart_items",
        "orders",
        "order_items",
        "payment_attempts",
    }


def test_soopi_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="soopi",
        root=root,
        include_patterns=_PY_PATTERNS,
        ignore_patterns=_IGNORE,
        language_factory=_python_adapter,
        deep_factories=(_fastapi_adapter, _sqlalchemy_adapter),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.secret_leaked is False
    assert report.prohibited_hits == ()
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
