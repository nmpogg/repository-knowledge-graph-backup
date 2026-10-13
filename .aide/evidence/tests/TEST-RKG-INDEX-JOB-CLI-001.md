---
key: TEST-RKG-INDEX-JOB-CLI-001
type: test-evidence
group: evidence
system: SYS-RKG
revision: 1
captured_at: 2026-09-25
captured_against:
  artifacts:
    - { key: TASK-RKG-015, revision: 6 }
    - { key: FR-RKG-001, revision: 7 }
  code_commit: 668df4b
  pins:
    cpython: "3.12.5"
    kuzu: "0.11.3"
---

# TEST-RKG-INDEX-JOB-CLI-001

Verified code commit `668df4b` on `feat/task-rkg-015-index-job-cli`.

| Check | Result |
| --- | --- |
| `python -m pytest -q` | 98 passed, 1 skipped |
| `ruff check src tests` | passed |
| `git diff --check` | passed |
| `uv run --offline --python .venv/Scripts/python.exe rkg --help` | CLI entry point runs |

`tests/integration/test_index_coordinator.py` covers re-index with retained old
snapshot and removed old entity, failed file limit with active pointer preserved,
parse error plus oversized-file warnings, report totals and per-file diagnostic,
single-writer rejection, startup recovery, repository creation with redacted
locator, CLI index and snapshot lookup, loopback validation, and FastAPI
application selection/binding. The storage lifecycle suite covers repository
revision and snapshot/repository activation and delete guards used by the CLI.

This verifies the service and CLI portions of AC-RKG-008/012/034/038/049/050/
055/067-071. `serve` currently binds a one-worker loopback health listener;
API routes and their shared response checks belong to TASK-RKG-016. The
reference-corpus wall-time/RAM benchmark in AC-RKG-039 remains for
TASK-RKG-022 after the pilot corpus is selected.
