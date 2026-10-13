---
key: PLAN-TASK-RKG-022-r4
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-022
revision: 1
plan_date: '2026-10-07'
change_set: CHG-RKG-2026-001
provenance: agent-eval-subset-confirmed-a
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - key: OBS-RKG-001
    revision: 2
    hash: 779e2f6001bd3aab1c4e04ad961a6e9fa65f28e88bbb677180b90a4c698e18f5
  - key: EVAL-RKG-QA-001
    revision: 2
    hash: cdc5746ac8da29aa0d2420f300f26579fcf84d8ddae958bb33a590e5e2db1529
  prior_plan: PLAN-TASK-RKG-022.md
---

# PLAN-TASK-RKG-022-r4 — Eval subset (no pilot)

Operator confirmed option (a): census + regression only. Pilot review, live Q&A
and perf remain blocked (`../pilot_fastapi` missing; owner adjudication pending).

## Thứ tự

1. `fixture census` — `pytest tests/evaluation/test_*_census.py -q` against
   `expected_*.json` oracles. Kiểm: per-fixture TP/FN/FP, coverage/precision,
   method/version/omissions; no absolute paths or secrets in report.
2. `regression` — `pytest tests -q` (expect pilot/OpenRouter skips) and
   frontend `npm test` / lint / `tsc -b` when needed. Kiểm: suite green or
   recorded skips; append evidence, do not erase prior reports.

## Không làm

- Không chạy `run_pilot_review.py`, `run_pilot_qa.py`, `run_pilot_benchmark.py`.
- Không waive KPI/NFR; không đóng gate; không sửa threshold hay expected sau khi xem fail.
- Không sửa normative spec; thiếu credential/pilot/owner → dừng / OQ.
