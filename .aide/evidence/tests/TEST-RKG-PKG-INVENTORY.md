---
key: TEST-RKG-PKG-INVENTORY
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-007
captured_at: 2026-09-25
code_revision: 4e902ebd2e86dbfe8a7afd8e491ecaf25a73168e
artifacts:
  - { key: TASK-RKG-007, revision: 4 }
  - { key: FR-RKG-002, revision: 8 }
---

# TEST-RKG-PKG-INVENTORY

Current-tree verification on the code revision above:

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_python_metadata.py -q` | 5 passed |
| `pytest -q` | 59 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |

The five focused cases cover declaration and lock version provenance, optional and
Poetry groups, markers, requirements include cycles, dynamic metadata diagnostics,
lock-only dependencies, direct/aliased/symbol imports, local shadowing, unknown
distribution names, nested callable ownership and absence of external call edges.
Each case also runs the shared language adapter conformance suite (all cases pass).
The skipped suite case is the pre-existing Windows symlink test.

AC-RKG-021 is verified for local shadowing and explicit import/distribution mapping;
deep adapter capability classification remains in TASK-RKG-008. AC-RKG-022 is
verified for the static metadata profile and callable usage facts at adapter level.
