import json
from pathlib import Path

from tools.aide_yaml import parse_document
from tools.change_set_document import load_change_set
from tools.write_traceability import write_traceability

ROOT = Path(__file__).resolve().parents[2]
LEGACY_JSON = """
{
  "key": "CHG-RKG-2026-004",
  "revision": 5,
  "status": "draft",
  "tier": "T2",
  "flow": "change",
  "phase": "implementation_complete_independent_review_passed_pending_gate_decision",
  "relations": {"satisfies": ["AC-RKG-001"]}
}
"""


def test_legacy_json_and_yaml_keep_change_set_fields(tmp_path):
    parsed = parse_document(LEGACY_JSON)
    assert parsed["status"] == "draft"
    assert parsed["revision"] == 5
    assert parsed["tier"] == "T2"
    assert parsed["flow"] == "change"
    assert parsed["phase"].startswith("implementation_complete")
    assert parsed["relations"]["satisfies"] == ["AC-RKG-001"]

    target = tmp_path / "change-set.yaml"
    target.write_text(
        "\n".join(
            [
                "key: CHG-RKG-2026-004",
                "revision: 5",
                "status: draft",
                "tier: T2",
                "flow: change",
                "phase: implementation_complete_independent_review_"
                "passed_pending_gate_decision",
                "relations:",
                "  satisfies:",
                "  - AC-RKG-001",
                "",
            ]
        ),
        encoding="utf-8",
    )
    loaded = load_change_set(target)
    assert loaded["key"] == parsed["key"]
    assert loaded["status"] == "draft"
    assert loaded["revision"] == parsed["revision"]
    assert loaded["tier"] == parsed["tier"]
    assert loaded["flow"] == parsed["flow"]
    assert loaded["phase"] == parsed["phase"]
    assert loaded["relations"]["satisfies"] == ["AC-RKG-001"]


def test_repository_change_sets_are_yaml_and_keep_recorded_status():
    folder = ROOT / ".aide/lifecycle/change-sets"
    for path in sorted(folder.glob("*/change-set.yaml")):
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        assert not text.startswith("{"), path.name
        loaded = load_change_set(path)
        assert loaded["status"] == "draft"
        assert isinstance(loaded["revision"], int)
        assert loaded["tier"] in {"T1", "T2", "T3"}
        assert isinstance(loaded["flow"], str)


def test_traceability_records_gaps_and_does_not_invent_passed(tmp_path):
    aide = tmp_path / ".aide"
    _write(
        aide / "requirements/fr/FR-RKG-001.md",
        """---
key: FR-RKG-001
status: approved
relations:
  satisfies: [GOAL-RKG-001]
  constrained_by: [NFR-RKG-SEC-001]
---
#### AC-RKG-001
- `validated_by:` [TEST-RKG-OK]
#### AC-RKG-002
- `validated_by:` [TEST-RKG-MISSING]
#### AC-RKG-003
- `constrained_by:` [NFR-RKG-SEC-001]
""",
    )
    _write(
        aide / "product/prd/PRD-RKG.md",
        "| GOAL-RKG-001 | direction |\n",
    )
    _write(
        aide / "requirements/nfr/NFR-RKG-SEC-001.md",
        "---\nkey: NFR-RKG-SEC-001\nstatus: approved\n---\n",
    )
    _write(
        aide / "lifecycle/stories/STORY-RKG-001.md",
        "---\nkey: STORY-RKG-001\nstatus: done\nsatisfies: [AC-RKG-001]\n---\n",
    )
    _write(
        aide / "lifecycle/stories/STORY-RKG-016.md",
        "---\nkey: STORY-RKG-016\nstatus: deprecated\nsatisfies: []\n---\n",
    )
    _write(
        aide / "lifecycle/tasks/TASK-RKG-001.md",
        """---
key: TASK-RKG-001
status: done
story: STORY-RKG-001
relations:
  implements:
  - FR-RKG-001
  - FR-RKG-MISSING
---
""",
    )
    _write(
        aide / "tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md",
        "---\nkey: API-RKG-CORE-v1\nstatus: draft\n"
        "relations:\n  satisfies: [FR-RKG-001]\n---\n",
    )
    _write(
        aide / "tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md",
        "---\nkey: TBL-RKG-GRAPH\nstatus: draft\n---\n",
    )
    _write(
        aide / "evidence/tests/TEST-RKG-OK.md",
        "---\nkey: TEST-RKG-OK\nstatus: draft\n---\n",
    )

    output = tmp_path / "traceability"
    stamp = "2026-10-13T00:00:00+00:00"
    first = write_traceability(
        tmp_path, code_tree="abc123", generated_at=stamp, output_dir=output
    )
    first_bytes = {path.name: path.read_bytes() for path in first}
    second = write_traceability(
        tmp_path, code_tree="abc123", generated_at=stamp, output_dir=output
    )
    assert [path.name for path in first] == [path.name for path in second]
    assert {path.name: path.read_bytes() for path in second} == first_bytes
    names = sorted(path.name for path in output.glob("TRC-*.json"))
    assert "TRC-story-STORY-RKG-016.json" not in names
    assert names == [
        "TRC-contract-API-RKG-CORE-v1.json",
        "TRC-contract-TBL-RKG-GRAPH.json",
        "TRC-coverage-SYS-RKG.json",
        "TRC-fr-FR-RKG-001.json",
        "TRC-story-STORY-RKG-001.json",
        "TRC-task-TASK-RKG-001.json",
    ]
    records = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in output.glob("TRC-*.json")
    }
    assert all(
        record["status"] != "passed" for record in records.values()
    )
    fr = records["TRC-fr-FR-RKG-001.json"]
    assert fr["code_tree"] == "abc123"
    assert fr["links"]["satisfies"] == ["GOAL-RKG-001"]
    assert fr["links"]["validated_by"] == ["TEST-RKG-OK", "TEST-RKG-MISSING"]
    assert {"reason": "missing_file", "key": "TEST-RKG-MISSING"} in fr["gaps"]
    assert {"reason": "missing_story", "key": "AC-RKG-002"} in fr["gaps"]
    assert {"reason": "missing_story", "key": "AC-RKG-003"} in fr["gaps"]
    assert {"reason": "missing_test", "key": "AC-RKG-002"} in fr["gaps"]
    assert {"reason": "missing_test", "key": "AC-RKG-003"} in fr["gaps"]
    assert {"reason": "missing_test", "key": "AC-RKG-001"} not in fr["gaps"]
    task = records["TRC-task-TASK-RKG-001.json"]
    assert task["links"]["story"] == ["STORY-RKG-001"]
    assert task["links"]["implements"] == ["FR-RKG-001", "FR-RKG-MISSING"]
    assert task["gaps"] == [{"reason": "missing_file", "key": "FR-RKG-MISSING"}]
    coverage = records["TRC-coverage-SYS-RKG.json"]
    assert coverage["counts"] == {"passed": 0, "failed": 0, "not_run": 5}
    assert coverage["status"] == "not_run"
    assert any(gap["key"] == "FR-RKG-MISSING" for gap in coverage["gaps"])


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
