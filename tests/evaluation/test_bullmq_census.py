"""OBS-RKG-001 census for repo-test/rkg-fixture-bullmq-worker.

Oracle: README Message channels, callables/edges, config keys, negatives.
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

EXPECTED = Path(__file__).with_name("expected_bullmq.json")
FIXTURE = "repo-test/rkg-fixture-bullmq-worker"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _bullmq_adapter():
    from rkg.adapters.bullmq_messaging import BullMQMessagingAdapter

    return BullMQMessagingAdapter()


def test_expected_oracle_loads() -> None:
    payload = load_expected(EXPECTED)
    assert payload["fixture_id"] == "rkg-fixture-bullmq-worker"
    assert payload["entities"]
    assert payload["edges"]
    assert any(
        item.get("qualified_name") == "order-processing"
        for item in payload["entities"]
    )


def test_bullmq_census_matches_expected(capsys: pytest.CaptureFixture[str]) -> None:
    expected = load_expected(EXPECTED)
    root = fixture_root(FIXTURE)
    batch = run_language_pipeline(
        repository_id="rkg-fixture-bullmq-worker",
        root=root,
        include_patterns=_TS_PATTERNS,
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        language_factory=_typescript_adapter,
        deep_factories=(_bullmq_adapter,),
    )
    report = compare_census(expected, batch)
    print(format_report(report))
    captured = capsys.readouterr().out
    assert SECRET not in captured
    assert str(root) not in captured
    assert report.outcome == "pass", format_report(report)
    assert report.coverage == 1.0
    assert report.precision == 1.0
