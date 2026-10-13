"""The corpus must fail closed on stale sources or broken evaluation bindings."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from evaluation.validate import GoldenValidationError, source_manifest, validate_dataset

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def dataset():
    return json.loads(Path(__file__).with_name("golden_set.json").read_text())


def test_checked_corpus_has_fifty_cases_and_six_repositories(dataset):
    summary = validate_dataset(dataset, ROOT)
    assert summary["cases"] == 50
    assert summary["turns"] == 73
    assert sum(summary["repositories"].values()) == 50
    assert summary["categories"]["answerable"] == 29
    assert summary["categories"]["conversation"] == 10
    assert summary["source_pins_valid"] is True
    assert summary["independent_review_status"] == "pending"
    assert summary["chatbot_evaluation_run"] is False


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("duplicate_case", "duplicate_or_missing_case_id"),
        ("foreign_source", "foreign_source_reference"),
        ("stale_source_hash", "stale_source_file"),
        ("invalid_range", "invalid_source_range"),
        ("unsafe_path", "unsafe_relative_path"),
        ("missing_history_expectation", "missing_history_truncation_expectation"),
        ("invalid_selection", "selection_without_clarification"),
    ],
)
def test_invalid_bindings_do_not_pass(dataset, mutation, error):
    value = deepcopy(dataset)
    first = value["cases"][0]
    if mutation == "duplicate_case":
        value["cases"][1]["id"] = first["id"]
    elif mutation == "foreign_source":
        first["turns"][0]["expected"]["required_facts"][0]["source_ids"] = ["S999"]
    elif mutation == "stale_source_hash":
        first["sources"][0]["file_sha256"] = "0" * 64
    elif mutation == "invalid_range":
        first["sources"][0]["end_line"] = 99999
    elif mutation == "unsafe_path":
        first["sources"][0]["path"] = "../outside.py"
    elif mutation == "missing_history_expectation":
        long_case = next(
            c for c in value["cases"] if c["category"] == "long_conversation"
        )
        long_case["turns"][-1]["expected"]["required_metadata"] = {}
    elif mutation == "invalid_selection":
        first["turns"][0]["selection"] = {
            "entity_type": "Callable",
            "symbol": "AuthService.logout",
            "path": "app/services/auth_service.py",
        }
    with pytest.raises(GoldenValidationError, match=error):
        validate_dataset(value, ROOT)


def test_new_source_files_are_visible_and_never_executed(tmp_path):
    source = tmp_path / "fixture.py"
    source.write_text("raise RuntimeError('fixture code must never execute')\n")
    before = source_manifest(tmp_path)
    assert set(before) == {"fixture.py"}
    extra = tmp_path / "new_feature.ts"
    extra.write_text("throw new Error('fixture code must never execute');\n")
    after = source_manifest(tmp_path)
    assert set(after) == {"fixture.py", "new_feature.ts"}
    assert before != after


def test_structural_validation_does_not_mark_review_approved(dataset):
    original = deepcopy(dataset)
    validate_dataset(dataset, ROOT)
    assert dataset == original
