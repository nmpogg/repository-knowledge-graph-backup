---
key: PLAN-TASK-RKG-044
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-044
revision: 1
plan_date: '2026-10-07'
change_set: CHG-RKG-2026-001
provenance: stack-c-normative-align
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
---

# PLAN-TASK-RKG-044 — Remaining verify only

Normative alignment for Stack C is settled. Remaining work is verification
evidence only — no new extractors.

Census-focused path: `test_bullmq_census.py` / `expected_bullmq.json` (no
separate BullMQ conformance suite in tree).

## Thứ tự

1. `census` — `pytest tests/evaluation/test_bullmq_census.py -q`.
2. `evidence` — append test evidence under `evidence/tests/` linking results
   (relative paths only); do not erase prior reports.

## Không làm

- New extractors or adapter modules under `src/`.
- Deep-support promotion.
- Vue/Nuxt/React Router/Java/Go adapters.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
