---
key: DIARY-TASK-RKG-022-r3
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
provenance: agent-eval-subset-a
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  plan: PLAN-TASK-RKG-022-r4.md
  artifacts:
  - key: OBS-RKG-001
    revision: 2
    hash: 779e2f6001bd3aab1c4e04ad961a6e9fa65f28e88bbb677180b90a4c698e18f5
  - key: EVAL-RKG-QA-001
    revision: 2
    hash: cdc5746ac8da29aa0d2420f300f26579fcf84d8ddae958bb33a590e5e2db1529
prior_evidence:
- evidence/plans/PLAN-TASK-RKG-022-r4.md
- evidence/tests/TEST-RKG-FIXTURE-CENSUS-001.json
- evidence/tests/TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md
- evidence/tests/TEST-RKG-EXTRACTION-FIXTURES-001-r2.md
- evidence/tests/TEST-RKG-FINAL-REGRESSION-002.md
---

# DIARY-TASK-RKG-022-r3 — Subset eval (census + regression)

## Diễn giải

- Operator confirmed option (a): run fixture census + regression only.
- `../pilot_fastapi` missing → skipped `run_pilot_review.py`,
  `run_pilot_qa.py`, `run_pilot_benchmark.py`.
- Wrote `PLAN-TASK-RKG-022-r4` before execution.

## Kết quả

1. Census: 12 pytest passed; aggregate TP=296 FN=0 FP=0; coverage/precision 1.0
   on six `repo-test` oracles. Evidence:
   `TEST-RKG-FIXTURE-CENSUS-001.json` + `TEST-RKG-FIXTURE-CENSUS-SUMMARY-001`.
2. Correction append: `TEST-RKG-EXTRACTION-FIXTURES-001-r2` (prior “unmeasured”
   claim superseded for current-tree census only).
3. Regression: pytest 246 passed / 7 skipped; frontend 77 passed; `tsc` pass;
   `ruff check` failed (17 E501). Evidence: `TEST-RKG-FINAL-REGRESSION-002`.

## Đi chệch

- None from plan scope. Ruff failure recorded as failed, not fixed (out of
  eval-only scope).

## Câu hỏi mở

- Pilot path + owner TP/FP adjudication for KPI-002.
- Live OpenRouter QA re-pin on HEAD for OBS-005 (credential in process env).
- Perf re-run + host ≥8 GiB for NFR-PERF eligibility.
- EVAL-RKG-QA-001 still `draft`; oracle review receipt; mandatory-pattern set
  confirmation for KPI-001 gate language.

## Không làm

- Không đóng gate; không waive KPI/NFR; không sửa normative spec.
