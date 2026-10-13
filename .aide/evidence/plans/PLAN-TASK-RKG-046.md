---
key: PLAN-TASK-RKG-046
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-046
revision: 1
plan_date: '2026-10-08'
change_set: CHG-RKG-2026-001
provenance: go-stack-code-verify
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
---

# PLAN-TASK-RKG-046 — Remaining verify only

Normative alignment for Go + kafka-go + pgx is settled. Remaining work is
verification evidence only.

## Thứ tự

1. `go-stack` — `pytest tests/conformance/test_go_stack.py -v`.
2. `go-census` — `pytest tests/evaluation/test_go_census.py -v`.
3. `evidence` — append test evidence under `evidence/tests/` linking results
   (relative paths only); do not erase prior reports.

## Không làm

- New extractors or adapter modules under `src/`.
- Other stacks (TypeScript, Vue, BullMQ, Java/Spring).
- Deep-support promotion.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
