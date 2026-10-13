---
key: TEST-RKG-PILOT-CORPUS-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  base_commit: d94aff5443c57070842fa4984bdadc99920bc75a
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
  corpus_test_sha256: 131a1a99491842516ef7c725d644d8d182e385e97b00771d3c0a169e723c5091
  artifacts:
    - { key: OQ-RKG-002, revision: 5 }
    - { key: TASK-RKG-022, revision: 5 }
---

# TEST-RKG-PILOT-CORPUS-001 — Pilot selection and source inventory

The selected pilot is `pilot_fastapi/` at version 0.1.0. It was authored in
this workspace for RKG. The project team can inspect and review its complete
source without third-party repository access or credentials. It has 17
application Python files and 1,132 application lines, below the 50,000 LOC
pilot ceiling. The locked standalone environment uses FastAPI 0.141.1,
SQLAlchemy 2.1.1 and aiokafka 0.14.0.

The RKG language, FastAPI, SQLAlchemy and aiokafka static adapters ran against
the pilot's source manifest. Distinct emitted edges with evidence in
`pilot/domains/` were counted per group; configuration and declared DI were
separated by target entity type. These are candidate facts for Task 22 manual
review, not precision results.

| Edge group | Source-backed candidate edges | Task 22 minimum |
| --- | ---: | ---: |
| imports | 36 | 30 |
| calls | 48 | 30 |
| declared DI to callable | 48 | 30 |
| DB maps_to | 12 | 10 |
| DB reads | 12 | 10 |
| DB writes | 12 | 10 |
| event publishes | 12 | 10 |
| event consumes | 12 | 10 |
| configuration depends_on | 12 | 10 |
| implements | 12 | 10 |

| Check | Result |
| --- | --- |
| `pytest tests/integration/test_pilot_corpus.py -q` | 1 passed |
| `pilot_fastapi/.venv/Scripts/python.exe -m pytest -q` from pilot directory | 1 passed |
| Full RKG `pytest -q` | 133 passed, 4 skipped |
| `ruff check pilot_fastapi tests/integration/test_pilot_corpus.py` | pass |
| Regenerate `pilot/domains/orders.py` | identical SHA-256 before/after |

The pilot tree digest covers 23 files. Compute it by sorting regular files
under `pilot_fastapi/`, excluding `.venv`, `__pycache__`, `.pytest_cache`,
`.db` and `.pyc`; for each file append its relative POSIX path, one NUL byte,
and the raw SHA-256 digest of its content to a SHA-256 accumulator. The
separate test digest is the SHA-256 of
`tests/integration/test_pilot_corpus.py`.

The source is purpose-built and its 12 domain modules share a template. Task
22 must disclose this limitation, manually review sampled facts, and perform
the fixture, Q&A, conversation, benchmark and adapter-conformance work. This
record establishes corpus availability only.
