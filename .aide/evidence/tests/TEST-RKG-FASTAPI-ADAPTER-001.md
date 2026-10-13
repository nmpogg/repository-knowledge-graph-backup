---
key: TEST-RKG-FASTAPI-ADAPTER-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-009
captured_at: 2026-09-25
code_revision: ca69624fb4f810955f38ffa3111d5873bfa743c2
artifacts:
  - { key: TASK-RKG-009, revision: 4 }
  - { key: FR-RKG-002, revision: 8 }
  - { key: NFR-RKG-EXT-001, revision: 3 }
---

# TEST-RKG-FASTAPI-ADAPTER-001

Current-tree verification on the code revision above:

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_fastapi_framework.py -q` | 6 passed |
| `pytest -q` | 81 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |
| Shared `run_framework_conformance` | 100% in every focused fixture |

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-004 / `TEST-RKG-ENDPOINT-EXTRACTION` | Direct app, nested and unattached routers, repeated same-prefix registration, multi-method route, trailing slash and path parameter, handler and chain identities |
| AC-RKG-005 / `TEST-RKG-DECLARED-DEPENDENCY` | App/router/include/decorator/parameter/default/annotation/sub-dependency links, with no declared dependency turned into `calls` |
| AC-RKG-006 / `TEST-RKG-NO-GUESS` | Dynamic path, duplicate handler binding, unattached router, local FastAPI shadow, router cycle and multiple apps produce no guessed endpoint |
| AC-RKG-007 / `TEST-RKG-EVIDENCE` | Every focused result passes `validate_fact_batch`; endpoint exposure, handler and dependency edges have source evidence and stable IDs |
| NFR-RKG-EXT-001 / `TEST-RKG-ADAPTER-CONFORMANCE` | Framework contract and deterministic output pass the shared conformance runner |

The one skipped suite case is the pre-existing Windows symlink test. These checks
cover the framework adapter boundary. Job publication and snapshot persistence are
part of TASK-RKG-015.
