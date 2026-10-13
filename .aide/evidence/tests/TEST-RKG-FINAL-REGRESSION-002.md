---
key: TEST-RKG-FINAL-REGRESSION-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-10-07
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  pins:
    cpython: "3.12.14"
    host: Windows AMD64
  plan: PLAN-TASK-RKG-022-r4.md
  prior_regression: TEST-RKG-FINAL-REGRESSION-001.md
---

# TEST-RKG-FINAL-REGRESSION-002 — Subset eval regression

Append-only regression after fixture census on current tree. Does not re-run
pilot review, live Q&A, or perf benchmarks. Does not erase
`TEST-RKG-FINAL-REGRESSION-001`.

## Kết quả

| Check | Result |
| --- | --- |
| `uv run pytest tests/evaluation/test_*_census.py -v` | 12 passed |
| `uv run pytest tests -q` | 246 passed, 7 skipped |
| `uv run ruff check src tests` | **failed** — 17× E501 (line length > 88) in existing tests |
| `npm test` (`frontend`) | 13 files, 77 passed |
| `npm run lint` (`frontend`) | exit 0, existing oxlint warnings |
| `npx tsc -b` (`frontend`) | pass |

Pytest warning: existing Starlette `TestClient` deprecation.

## Skips on this host

| Test | Reason |
| --- | --- |
| `tests/integration/test_openrouter_live.py` | OpenRouter credential unavailable (process env) |
| `tests/integration/test_grounded_qa_live.py` (2) | OpenRouter credential unavailable (process env) |
| `tests/integration/test_pilot_corpus.py` (2) | sibling pilot repository unavailable |
| `tests/integration/test_core_api.py` (symlink) | creating symlinks not permitted |
| `tests/unit/test_local_source.py` (symlink) | creating symlinks not permitted |

## Still out of this subset

- KPI-RKG-002 owner adjudication (`TEST-RKG-PILOT-REVIEW-SUMMARY-001`).
- OBS-RKG-005 live re-run on HEAD (`TEST-RKG-QA-EVAL-SUMMARY-001` last live = r6 on older commit).
- NFR-RKG-PERF-001 re-run / reference-host eligibility (`TEST-RKG-PERF-SUMMARY-001`).
- No KPI/NFR waiver; no gate close.
