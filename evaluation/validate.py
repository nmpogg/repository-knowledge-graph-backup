"""Validate corpus structure and source pins without executing fixture code."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath

import jsonschema

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".vue", ".java", ".go"}
IGNORED_PARTS = {
    ".git",
    "node_modules",
    "dist",
    "target",
    "build",
    ".nuxt",
    ".output",
    "__pycache__",
}
REPOSITORY_COUNTS = {
    "soopi": 10,
    "rkg-fixture-react-ts": 8,
    "rkg-fixture-bullmq-worker": 8,
    "rkg-fixture-spring-orders": 8,
    "rkg-fixture-go-event-worker": 8,
    "rkg-fixture-nuxt4": 8,
}
CATEGORY_COUNTS = {
    "answerable": 29,
    "insufficient": 4,
    "ambiguous": 1,
    "safety": 5,
    "conversation": 10,
    "long_conversation": 1,
}


class GoldenValidationError(ValueError):
    pass


def check(condition: bool, code: str) -> None:
    if not condition:
        raise GoldenValidationError(code)


def relative_path(value: str) -> Path:
    path = PurePosixPath(value)
    check(
        bool(value)
        and not path.is_absolute()
        and path.as_posix() == value
        and ".." not in path.parts
        and "\\" not in value
        and ":" not in value
        and all(ord(c) >= 32 for c in value),
        "unsafe_relative_path",
    )
    return Path(*path.parts)


def source_manifest(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            not path.is_file()
            or path.suffix not in SOURCE_SUFFIXES
            or set(relative.parts) & IGNORED_PARTS
        ):
            continue
        check(path.resolve().is_relative_to(root.resolve()), "source_outside_fixture")
        result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def validate_dataset(dataset: dict, repository_root: Path) -> dict:
    schema = json.loads(Path(__file__).with_name("golden_set.schema.json").read_text())
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(dataset))
    if errors:
        pointer = "/".join(str(part) for part in errors[0].absolute_path)
        raise GoldenValidationError(f"invalid_schema:{pointer}:{errors[0].validator}")
    cases = dataset["cases"]
    check(
        {c["id"] for c in cases} == {f"RKG-EVAL-{i:03}" for i in range(1, 51)},
        "duplicate_or_missing_case_id",
    )
    check(
        Counter(c["repository"] for c in cases) == REPOSITORY_COUNTS,
        "unexpected_repository_distribution",
    )
    check(
        Counter(c["category"] for c in cases) == CATEGORY_COUNTS,
        "unexpected_category_distribution",
    )
    check(set(dataset["repositories"]) == set(REPOSITORY_COUNTS), "unknown_repository")
    total_pins = 0
    for repo, item in dataset["repositories"].items():
        check(item["root"] == f"repo-test/{repo}", "repository_root_mismatch")
        base = repository_root / relative_path(item["root"])
        check(
            base.resolve().is_relative_to(repository_root.resolve()), "unsafe_repo_root"
        )
        for name in item["files"]:
            relative_path(name)
        actual = source_manifest(base)
        check(actual == item["files"], f"stale_source_manifest:{repo}")
        encoded = json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()
        check(
            hashlib.sha256(encoded).hexdigest() == item["source_manifest_sha256"],
            f"invalid_manifest_digest:{repo}",
        )
        total_pins += len(actual)
    for case in cases:
        case_id = case["id"]
        base = repository_root / dataset["repositories"][case["repository"]]["root"]
        evidence = {item["id"]: item for item in case["sources"]}
        check(len(evidence) == len(case["sources"]), f"duplicate_source_id:{case_id}")
        for item in evidence.values():
            path = base / relative_path(item["path"])
            check(
                path.resolve().is_relative_to(base.resolve()), "source_outside_fixture"
            )
            check(path.is_file(), f"missing_source:{case_id}:{item['id']}")
            data = path.read_bytes()
            check(
                hashlib.sha256(data).hexdigest() == item["file_sha256"],
                f"stale_source_file:{case_id}:{item['id']}",
            )
            lines = data.decode("utf-8").splitlines(keepends=True)
            start, end = item["start_line"], item["end_line"]
            check(1 <= start <= end <= len(lines), f"invalid_source_range:{case_id}")
            span = "".join(lines[start - 1 : end]).encode()
            check(
                hashlib.sha256(span).hexdigest() == item["span_sha256"],
                f"stale_source_range:{case_id}:{item['id']}",
            )
            check(
                item["path"] in dataset["repositories"][case["repository"]]["files"],
                f"source_not_pinned:{case_id}:{item['id']}",
            )
        turns = case["turns"]
        if case["category"] == "conversation":
            check(2 <= len(turns) <= 4, f"invalid_conversation_length:{case_id}")
        elif case["category"] == "long_conversation":
            check(len(turns) >= 9, f"short_history_case:{case_id}")
            check(
                turns[-1]["expected"]["required_metadata"].get("history_truncated")
                is True,
                "missing_history_truncation_expectation",
            )
        else:
            check(len(turns) == 1, f"standalone_case_has_multiple_turns:{case_id}")
        expected_status = {
            "answerable": "answered",
            "insufficient": "insufficient_evidence",
            "ambiguous": "needs_clarification",
            "safety": "answered",
        }.get(case["category"])
        if expected_status:
            check(
                turns[0]["expected"]["status"] == expected_status,
                f"category_status_mismatch:{case_id}",
            )
        used_sources = set()
        for number, turn in enumerate(turns, 1):
            check(turn["turn_id"] == f"T{number}", f"invalid_turn_sequence:{case_id}")
            facts = turn["expected"]["required_facts"]
            check(
                len({f["id"] for f in facts}) == len(facts), f"duplicate_fact:{case_id}"
            )
            for index, fact in enumerate(facts, 1):
                check(fact["id"] == f"T{number}-F{index}", f"invalid_fact_id:{case_id}")
                check(
                    set(fact["source_ids"]) <= evidence.keys(),
                    f"foreign_source_reference:{case_id}:{fact['id']}",
                )
                used_sources.update(fact["source_ids"])
            if "selection" in turn:
                check(
                    number > 1
                    and turns[number - 2]["expected"]["status"]
                    == "needs_clarification",
                    f"selection_without_clarification:{case_id}",
                )
                relative_path(turn["selection"]["path"])
                check(
                    any(
                        s["path"] == turn["selection"]["path"]
                        for s in evidence.values()
                    ),
                    f"selection_without_source:{case_id}",
                )
        check(used_sources == evidence.keys(), f"unreferenced_source:{case_id}")
    return {
        "cases": len(cases),
        "turns": sum(len(c["turns"]) for c in cases),
        "repositories": dict(Counter(c["repository"] for c in cases)),
        "categories": dict(Counter(c["category"] for c in cases)),
        "pinned_source_files": total_pins,
        "source_pins_valid": True,
        "independent_review_status": dataset["independent_review_status"],
        "chatbot_evaluation_run": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=Path(__file__).with_name("golden_set.json")
    )
    args = parser.parse_args()
    try:
        dataset = json.loads(args.cases.read_text(encoding="utf-8"))
        summary = validate_dataset(dataset, Path(__file__).resolve().parents[1])
    except (GoldenValidationError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        code = (
            str(exc) if isinstance(exc, GoldenValidationError) else type(exc).__name__
        )
        print(json.dumps({"valid": False, "error": code}, ensure_ascii=False))
        return 1
    print(json.dumps({"valid": True, **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
