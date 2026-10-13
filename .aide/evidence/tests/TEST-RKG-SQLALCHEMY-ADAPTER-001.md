---
key: TEST-RKG-SQLALCHEMY-ADAPTER-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-010
captured_at: 2026-09-25
code_revision: 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
artifacts:
  - { key: TASK-RKG-010, revision: 5 }
  - { key: FR-RKG-002, revision: 8 }
  - { key: REG-ADAPTER-001, revision: 5 }
  - { key: NFR-RKG-EXT-001, revision: 3 }
---

# TEST-RKG-SQLALCHEMY-ADAPTER-001

Current-tree verification. The checked implementation is the working tree on
top of the base revision above; file hashes are in `DIARY-TASK-RKG-010`.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_sqlalchemy_data.py -q` | 4 passed |
| `pytest -q` | 94 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |
| Shared `run_framework_conformance` | 100% in every focused fixture |

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-013 / `TEST-RKG-DB-MAPS` | Literal `__tablename__`, literal schema, omitted schema, and the same table name in another namespace stay distinct. Two models with the same namespace and table share one resource and two `maps_to` edges. Dynamic names, reflection and `automap_base` create no mapping |
| AC-RKG-014 / `TEST-RKG-DB-RW` | Executed `get`, `select`, `insert`, `update`, `delete` and `add` record operation rules on the `reads` or `writes` evidence for the resolved resource. Several writes to one resource stay one edge whose rule is the lexicographically smallest operation rule. A bare `select`, an unexecuted statement and an unresolved model do not create `reads` or `writes`; the unresolved model emits `sqlalchemy_model_unresolved`. A module-level call does not create `reads` |
| NFR-RKG-EXT-001 / `TEST-RKG-ADAPTER-CONFORMANCE` | Data-access contract and deterministic output pass the shared conformance runner. A compatible lock selects `rkg.sqlalchemy` without an application entrypoint. A 1.4 lock stays `unsupported_version` |

The skipped suite case is the pre-existing Windows symlink test. Pytest puts
both the repository root and `src` on `pythonpath`, so the conformance package
import resolves. Column values are not copied into facts. Job publication
remains part of TASK-RKG-015.
