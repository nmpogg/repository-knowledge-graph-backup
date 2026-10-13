---
key: TEST-RKG-CORE-API-001
type: test-evidence
group: evidence
system: SYS-RKG
revision: 1
captured_at: 2026-09-25
captured_against:
  artifacts:
    - { key: TASK-RKG-016, revision: 6 }
    - { key: API-RKG-CORE-v1, revision: 9 }
    - { key: FR-RKG-001, revision: 7 }
    - { key: FR-RKG-003, revision: 7 }
    - { key: FR-RKG-004, revision: 6 }
  base_commit: 548c5eded456820a8a579572a31538c69cb5e20d
  pins:
    cpython: "3.12.14"
    kuzu: "0.11.3"
---

# TEST-RKG-CORE-API-001

Verified on the working tree based on `548c5ed`.

| Check | Result |
| --- | --- |
| `uv run pytest tests -q` | 107 passed, 1 skipped |
| `uv run ruff check src tests` | passed |
| `git diff --check` | passed |

`tests/integration/test_core_api.py` covers repository create/list/patch/delete
with redacted locators, source-root rejection, revision conflict and immutable
source identity, index-job session and Origin rejection before a job row exists,
`succeeded_with_warnings` without a `partial` status, app selection that sticks
on the next index, single-writer `409 index_job_busy`, `Retry-After` until a
terminal job, search paging, subgraph direction, deterministic context, missing
active snapshot, unavailable snapshot, snapshot activate/delete guards,
unreferenced snapshot delete, `repository_in_use` then cascade delete,
repository list paging, retired path aliases, and conversation delete while a
turn is pending. `rkg serve` is checked to build
the FastAPI app on `127.0.0.1` and to reject a second worker.

This verifies the transport portion of AC-RKG-009/010/012/026/034/036/040/041/
044/045/055/058/060/061/066–072. AC-RKG-062 remains with TASK-RKG-022.
Conversation create, list and turn routes remain with TASK-RKG-021.
