"""Write generated traceability records from current `.aide/` artifacts.

Does not execute the test suite. A chain is `not_run` unless this process is
given an evidence result, which it never invents. Dangling keys and FR/AC
items with no current story or test file are gaps.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.aide_yaml import parse_document

LINK_FIELDS = (
    "satisfies",
    "implements",
    "covers",
    "constrained_by",
    "validated_by",
    "measured_by",
    "story",
    "epic",
    "change_set",
)
INACTIVE = {"deprecated", "retired", "superseded", "historical"}
_AC_HEADING = re.compile(r"^#### (AC-[A-Za-z0-9-]+)\s*$", re.M)
_AC_LINK = re.compile(
    r"`(validated_by|constrained_by):`\s*\[([^\]]*)\]",
)
_GOAL_ROW = re.compile(r"^\|\s*(GOAL-[A-Za-z0-9-]+)\s*\|", re.M)
_KEY_STEM = re.compile(r"^[A-Z][A-Z0-9]+(?:-[A-Za-z0-9]+)+$")


def write_traceability(
    root: Path,
    *,
    code_tree: str,
    generated_at: str,
    output_dir: Path | None = None,
) -> list[Path]:
    aide = root / ".aide"
    destination = output_dir or (aide / "generated" / "traceability")
    destination.mkdir(parents=True, exist_ok=True)
    for stale in destination.glob("TRC-*.json"):
        stale.unlink()

    indexed = _index(aide)
    records = [
        _chain(artifact, indexed, code_tree, generated_at)
        for artifact in _current_artifacts(aide)
    ]
    written: list[Path] = []
    for record in records:
        path = destination / f"TRC-{record['stage']}-{record['key']}.json"
        _dump(path, record)
        written.append(path)
    coverage = _coverage(records, code_tree, generated_at)
    coverage_path = destination / "TRC-coverage-SYS-RKG.json"
    _dump(coverage_path, coverage)
    written.append(coverage_path)
    return written


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    code_tree, generated_at = _git_identity(root)
    write_traceability(root, code_tree=code_tree, generated_at=generated_at)


def _git_identity(root: Path) -> tuple[str, str]:
    code_tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    generated_at = subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", "HEAD"], cwd=root, text=True
    ).strip()
    return code_tree, generated_at


def _current_artifacts(aide: Path) -> list[dict]:
    specs = [
        ("fr", "requirements/fr/FR-*.md"),
        ("story", "lifecycle/stories/STORY-*.md"),
        ("task", "lifecycle/tasks/TASK-*.md"),
        ("contract", "tech-specs/**/API-*.md"),
        ("contract", "tech-specs/**/TBL-*.md"),
    ]
    found: list[dict] = []
    for stage, pattern in specs:
        for path in sorted(aide.glob(pattern)):
            frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
            status = str(frontmatter.get("status") or "")
            if status in INACTIVE:
                continue
            key = str(frontmatter.get("key") or path.stem)
            found.append(
                {
                    "key": key,
                    "stage": stage,
                    "path": path,
                    "frontmatter": frontmatter,
                    "body": body,
                }
            )
    return found


def _chain(artifact: dict, indexed: dict, code_tree: str, generated_at: str) -> dict:
    links = _links(artifact["frontmatter"])
    criteria = []
    if artifact["stage"] == "fr":
        criteria = _acceptance_criteria(artifact["body"])
    for _ac, validated_by, constrained_by in criteria:
        links["validated_by"] = _extend(links.get("validated_by", []), validated_by)
        links["constrained_by"] = _extend(
            links.get("constrained_by", []), constrained_by
        )
    links = {field: values for field, values in links.items() if values}
    gaps = _gaps(artifact, links, criteria, indexed)
    return {
        "key": artifact["key"],
        "stage": artifact["stage"],
        "generated_at": generated_at,
        "code_tree": code_tree,
        "status": "not_run",
        "links": links,
        "gaps": gaps,
    }


def _gaps(artifact: dict, links: dict, criteria: list, indexed: dict) -> list[dict]:
    gaps: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(reason: str, key: str) -> None:
        marker = (reason, key)
        if marker not in seen:
            seen.add(marker)
            gaps.append({"reason": reason, "key": key})

    for values in links.values():
        for key in values:
            if key not in indexed["resolved"]:
                add("missing_file", key)
    if artifact["stage"] == "fr":
        covered = indexed["story_acceptance"]
        for ac, validated_by, _constrained in criteria:
            if ac not in covered:
                add("missing_story", ac)
            if not any(test in indexed["files"] for test in validated_by):
                add("missing_test", ac)
    gaps.sort(key=lambda item: (item["reason"], item["key"]))
    return gaps


def _coverage(records: list[dict], code_tree: str, generated_at: str) -> dict:
    counts = {"passed": 0, "failed": 0, "not_run": 0}
    gaps: list[dict] = []
    for record in records:
        counts[record["status"]] += 1
        for gap in record["gaps"]:
            gaps.append({"record": record["key"], **gap})
    gaps.sort(key=lambda item: (item["record"], item["reason"], item["key"]))
    status = "passed"
    if counts["failed"]:
        status = "failed"
    elif counts["not_run"] or counts["passed"] != len(records):
        status = "not_run"
    return {
        "key": "SYS-RKG",
        "stage": "coverage",
        "generated_at": generated_at,
        "code_tree": code_tree,
        "status": status,
        "counts": counts,
        "links": {},
        "gaps": gaps,
    }


def _index(aide: Path) -> dict:
    files: set[str] = set()
    resolved: set[str] = set()
    story_acceptance: set[str] = set()
    for path in sorted(aide.rglob("*")):
        if (
            not path.is_file()
            or "generated" in path.parts
            or path.suffix.lower() not in {".md", ".yaml", ".yml"}
        ):
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(text)
        key = frontmatter.get("key")
        if isinstance(key, str) and key:
            files.add(key)
            resolved.add(key)
        if _KEY_STEM.match(path.stem):
            files.add(path.stem)
            resolved.add(path.stem)
        if path.parent.name == "fr":
            for match in _AC_HEADING.finditer(body):
                resolved.add(match.group(1))
        for match in _GOAL_ROW.finditer(text):
            resolved.add(match.group(1))
        if (
            "lifecycle" in path.parts
            and path.parent.name == "stories"
            and str(frontmatter.get("status") or "") not in INACTIVE
        ):
            for ac in _links(frontmatter).get("satisfies", []):
                if ac.startswith("AC-"):
                    story_acceptance.add(ac)
    return {
        "files": files,
        "resolved": resolved,
        "story_acceptance": story_acceptance,
    }


def _links(node) -> dict[str, list[str]]:
    found = {field: [] for field in LINK_FIELDS}
    _walk_links(node, found)
    return {field: _dedupe(values) for field, values in found.items()}


def _walk_links(node, found: dict[str, list[str]]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in found:
                found[key].extend(_as_keys(value))
            else:
                _walk_links(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_links(item, found)


def _as_keys(value) -> list[str]:
    if value is None or value is False:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        keys: list[str] = []
        for item in value:
            keys.extend(_as_keys(item))
        return keys
    return []


def _acceptance_criteria(body: str) -> list[tuple[str, list[str], list[str]]]:
    parts = _AC_HEADING.split(body)
    criteria = []
    index = 1
    while index + 1 < len(parts):
        validated_by: list[str] = []
        constrained_by: list[str] = []
        for match in _AC_LINK.finditer(parts[index + 1]):
            keys = [item.strip() for item in match.group(2).split(",") if item.strip()]
            if match.group(1) == "validated_by":
                validated_by.extend(keys)
            else:
                constrained_by.extend(keys)
        criteria.append((parts[index], _dedupe(validated_by), _dedupe(constrained_by)))
        index += 2
    return criteria


def _split_frontmatter(text: str) -> tuple[dict, str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        try:
            parsed = parse_document(text)
        except (json.JSONDecodeError, ValueError):
            return {}, text
        return (parsed, "") if isinstance(parsed, dict) else ({}, text)
    lines = text.splitlines()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            parsed = parse_document("\n".join(lines[1:index]))
            body = "\n".join(lines[index + 1 :])
            return (parsed if isinstance(parsed, dict) else {}, body)
    return {}, text


def _extend(existing: list[str], extra: list[str]) -> list[str]:
    return _dedupe([*existing, *extra])


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _dump(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
