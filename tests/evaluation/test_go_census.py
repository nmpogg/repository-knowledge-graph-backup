"""OBS-RKG-001 census for repo-test/rkg-fixture-go-event-worker.

Oracle: README Go declarations, Kafka/pgx inventory, and negatives.
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

EXPECTED = Path(__file__).with_name("expected_go.json")
FIXTURE = "repo-test/rkg-fixture-go-event-worker"
_GO_PATTERNS = ("*.go", "**/*.go")


def _go_adapter():
    from rkg.adapters.go_language import GoLanguageAdapter

    return GoLanguageAdapter()


def _kafka_go_adapter():
    from rkg.adapters.kafka_go_messaging import KafkaGoMessagingAdapter

    return KafkaGoMessagingAdapter()


def _pgx_adapter():
    from rkg.adapters.pgx_data import PgxDataAccessAdapter

    return PgxDataAccessAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-go-event-worker"
    assert payload["entities"]
    assert payload["edges"]
    assert not any(item.get("type") == "Namespace" for item in payload["entities"])
    assert any(
        item.get("qualified_name") == "relational:commerce.order_projection"
        for item in payload["entities"]
    )


def test_go_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-go-event-worker",
        root=root,
        include_patterns=_GO_PATTERNS,
        ignore_patterns=("**/testdata/**",),
        language_factory=_go_adapter,
        deep_factories=(_kafka_go_adapter, _pgx_adapter),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
