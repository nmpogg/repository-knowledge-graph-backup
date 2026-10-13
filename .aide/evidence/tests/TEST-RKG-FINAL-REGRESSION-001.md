---
key: TEST-RKG-FINAL-REGRESSION-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-023
captured_at: 2026-09-28
captured_against:
  code_commit: 404f0572ee2eabda61bee535e6ac88e3ddb53fed
  pins:
    cpython: "3.12.14"
    host: Windows AMD64
    kuzu: "0.11.3"
---

# TEST-RKG-FINAL-REGRESSION-001 — Handoff regression

Regression xác nhận suite hiện có vẫn chạy sau khi runbook được viết. Nó
không đo lại KPI extraction, không chấm mẫu pilot và không chạy lại benchmark.

## Kết quả

| Check | Result |
| --- | --- |
| `uv run ruff check src tests` | pass |
| `uv run pytest tests -q` | 132 passed, 6 skipped |
| `npm test` (`frontend`) | 6 files, 27 passed |
| `npm run lint` (`frontend`) | exit 0, existing oxlint warnings |
| `npx tsc -b` (`frontend`) | pass |

Pytest emitted the existing Starlette `TestClient` deprecation warning.
No new failure was recorded.

## Skips on this host

| Test | Reason |
| --- | --- |
| `tests/integration/test_openrouter_live.py` | OpenRouter credential unavailable |
| `tests/integration/test_grounded_qa_live.py` (2) | OpenRouter credential unavailable |
| `tests/integration/test_pilot_corpus.py` (2) | sibling pilot repository is unavailable |
| `tests/unit/test_local_source.py` symlink case | creating symlinks is not permitted on this host |

Task 22 recorded 134 passed and 4 skipped when the pilot corpus was present.
This run does not replace `TEST-RKG-PILOT-CORPUS-001/002` or the eval and
benchmark reports.

## Scope delivered

Operator steps for setup, allowed local roots, index, loopback serve, session
token, LLM configuration, history window, snapshot/repository retention and
stable `error_code` handling are in `README.md`.

## Remaining risks

Carry these into MVP gate review. None is waived by this report.

- Fixture coverage and precision for KPI-RKG-001 are unmeasured
  (`TEST-RKG-EXTRACTION-FIXTURES-001`).
- Pilot edge labels await owner adjudication
  (`TEST-RKG-PILOT-REVIEW-SUMMARY-001`).
- Context p95 did not stay under the NFR-RKG-PERF-001 threshold in two
  published runs, and this host is not confirmed as the reference host
  (`TEST-RKG-PERF-SUMMARY-001`).
- Bulk snapshot cleanup exists only as `rkg.conversations.cleanup_snapshots`.
  There is no CLI or HTTP command for it.
- `history_truncated` is returned on the turn response and is not recomputed
  when history is reloaded (`DIARY-TASK-RKG-021`).
- Live Q&A was not re-executed here. The latest published live run remains
  `TEST-RKG-QA-EVAL-SUMMARY-001-r4`.
