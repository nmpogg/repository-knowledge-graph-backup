"""OBS-RKG-001 census for repo-test/rkg-fixture-spring-orders.

Oracle: README Java/Spring/JPA/Kafka inventory and intentional negatives.
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

EXPECTED = Path(__file__).with_name("expected_spring.json")
FIXTURE = "repo-test/rkg-fixture-spring-orders"
_JAVA_PATTERNS = ("*.java", "**/*.java", "*.yml", "**/*.yml", "*.yaml", "**/*.yaml")


def _java_adapter():
    from rkg.adapters.java_language import JavaLanguageAdapter

    return JavaLanguageAdapter()


def _spring_adapter():
    from rkg.adapters.spring_framework import SpringFrameworkAdapter

    return SpringFrameworkAdapter()


def _jpa_adapter():
    from rkg.adapters.jpa_data import JpaDataAccessAdapter

    return JpaDataAccessAdapter()


def _spring_kafka_adapter():
    from rkg.adapters.spring_kafka_messaging import SpringKafkaMessagingAdapter

    return SpringKafkaMessagingAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-spring-orders"
    assert payload["entities"]
    assert payload["edges"]
    resources = {
        item["qualified_name"]
        for item in payload["entities"]
        if item.get("type") == "DataResource"
    }
    assert resources == {
        "relational:commerce.orders",
        "relational:commerce.order_items",
        "relational:audit.orders",
    }


def test_spring_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-spring-orders",
        root=root,
        include_patterns=_JAVA_PATTERNS,
        ignore_patterns=("**/target/**", "**/.mvn/**"),
        language_factory=_java_adapter,
        deep_factories=(_spring_adapter, _jpa_adapter, _spring_kafka_adapter),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
