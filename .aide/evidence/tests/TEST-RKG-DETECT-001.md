---
key: TEST-RKG-DETECT-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-008
captured_at: 2026-09-25
code_revision: 51cede902a688529ebcd6ec164af7b3a86d826a0
artifacts:
  - { key: TASK-RKG-008, revision: 6 }
  - { key: FR-RKG-002, revision: 8 }
  - { key: NFR-RKG-EXT-001, revision: 3 }
  - { key: REG-ADAPTER-001, revision: 2 }
---

# TEST-RKG-DETECT-001

Current-tree verification on the code revision above:

| Check | Result |
| --- | --- |
| `pytest tests/unit/test_technology_detection.py -q` | 5 passed |
| `pytest -q` | 64 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |

| AC / contract | Evidence from focused tests |
| --- | --- |
| AC-RKG-020 | Declared-only, unknown version, unsupported version and supported-pattern reports with source evidence |
| AC-RKG-021 | Explicit import ownership and local shadowing; distinct adapter capabilities stay distinct |
| AC-RKG-040 | Ordered multiple app candidates, exact override validation and retained choice |
| AC-RKG-052 | Single module-level app candidate auto-selected |
| AC-RKG-053 | SQLAlchemy and aiokafka adapters both selected without application-choice conflict |
| AC-RKG-065 | Required framework app without a resolvable candidate returns `app_unresolved` |
| NFR-RKG-EXT-001 | Python language conformance 100%; custom detector/adapter selected without coordinator changes; no adapter-ID branch in `selection.py` |

The pre-existing Windows symlink case remains the one skipped suite test. These are
detector and selection-layer checks. Route/DI facts belong to T-009, and job failure,
snapshot publication and persisted app choice belong to T-015.
