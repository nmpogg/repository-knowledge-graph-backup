---
key: TEST-RKG-PILOT-CORPUS-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  base_commit: d94aff5443c57070842fa4984bdadc99920bc75a
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
  corpus_test_sha256: 9b86d55a36150ff7ffaa95349fc8218546a420175f8544bb3249ee929c7d8663
  artifacts:
    - { key: OQ-RKG-002, revision: 6 }
    - { key: TASK-RKG-022, revision: 6 }
---

# TEST-RKG-PILOT-CORPUS-002 — Sibling pilot relocation

The selected FastAPI source now lives in sibling `../pilot_fastapi/`, outside
the RKG repository. Its 23-file source tree digest is unchanged from
`TEST-RKG-PILOT-CORPUS-001`; the previous candidate-edge inventory therefore
still describes the exact same source revision. Its `.venv`, cache and local
SQLite file are excluded from the digest and from source scanning.

`tests/integration/test_pilot_corpus.py` now reads the sibling by default and
accepts an explicit `RKG_PILOT_REPO` path for other workspaces. It verifies the
pinned source digest before extracting facts, and restricts edge counts to
evidence under `pilot/domains/`. An unavailable default sibling is reported as
a skip in general RKG test runs; an explicitly configured missing path fails.
Task 22 must run this check with the chosen pilot present.

| Check | Result |
| --- | --- |
| Sibling source tree digest | matches `TEST-RKG-PILOT-CORPUS-001` |
| `pytest tests/integration/test_pilot_corpus.py -q` | 1 passed |
| `ruff check tests/integration/test_pilot_corpus.py` | pass |

The sibling directory has no `.git` metadata at capture time. The digest above
pins its contents for review; no Git commit is claimed for that directory.
The pilot remains a controlled synthetic corpus, and no Task 22 precision or
acceptance result is inferred from this relocation.
