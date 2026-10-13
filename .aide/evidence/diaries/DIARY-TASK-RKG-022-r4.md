---
key: DIARY-TASK-RKG-022-r4
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-022
revision: 1
implementation_window:
  from: '2026-10-07'
  through: '2026-10-07'
change_set: CHG-RKG-2026-001
provenance: agent-eval-subset-a-rerun
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  plan: PLAN-TASK-RKG-022-r4.md
  prior_diary: DIARY-TASK-RKG-022-r3.md
prior_evidence:
- evidence/tests/TEST-RKG-FIXTURE-CENSUS-001.json
- evidence/tests/TEST-RKG-FINAL-REGRESSION-002.md
---

# DIARY-TASK-RKG-022-r4 — Subset (a) re-verify + eval docs

## Diễn giải

Operator re-requested subset (a): census + regression only; no OpenRouter, no
`../pilot_fastapi`, no `run_pilot_*` / benchmark. Commit unchanged from r3 evidence.

## Kết quả chạy lại (2026-10-07)

| Check | Result |
| --- | --- |
| `uv run pytest tests/evaluation/ -k census -v` | 12 passed |
| `uv run pytest tests -q` | 246 passed, 7 skipped |
| `npm test` / `npm run lint` / `npx tsc -b` (frontend) | 77 passed; lint exit 0; tsc pass |
| `uv run ruff check src tests` | failed — 17× E501 (unchanged from REGRESSION-002) |

**Evidence append:** not required — `code_commit` matches
`TEST-RKG-FIXTURE-CENSUS-001` and `TEST-RKG-FINAL-REGRESSION-002`.

## Eval docs completed (subset a)

- Oracle review packet: `REV-RKG-EVAL-ORACLE-001`
- Pending receipt + oracle hashes: `RCPT-RKG-EVAL-ORACLE-001`
- Mandatory MVP / polyglot-06 in-out: `TEST-RKG-EXTRACTION-FIXTURES-001-r3`

## Handoff — still open

| Item | Status |
| --- | --- |
| Oracle receipt (`RCPT-RKG-EVAL-ORACLE-001`) | **pending** Tech Lead sign-off |
| KPI-RKG-002 pilot edge adjudication | **pending** owner (`TEST-RKG-PILOT-REVIEW-SUMMARY-001`) |
| OBS-RKG-005 / KPI-RKG-005 live Q&A on HEAD | **not_run** (no OpenRouter credential) |
| NFR-RKG-PERF-001 | **not_run** (no benchmark this subset; reference host unconfirmed) |
| `EVAL-RKG-QA-001` | **draft** — no new live eval fabricated |
| Polyglot monorepo fixture (`06`) | **out** of census until built + oracle |

## Không làm

- Không chạy pilot QA/review/benchmark; không bịa `TEST-RKG-QA-EVAL`.
- Không waive KPI/NFR; không đóng gate; không commit (unless operator asks).
