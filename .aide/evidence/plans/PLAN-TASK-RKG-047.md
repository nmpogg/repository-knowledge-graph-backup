---
key: PLAN-TASK-RKG-047
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-047
revision: 1
plan_date: '2026-10-08'
change_set: CHG-RKG-2026-001
provenance: flask-code-verify
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
---

# PLAN-TASK-RKG-047 — Remaining verify only

Normative alignment for Flask is settled. Remaining work is verification
evidence only.

## Thứ tự

1. `flask` — `pytest tests/conformance/test_flask_framework.py -v`.
2. `evidence` — append test evidence under `evidence/tests/` linking the run
   (relative paths only).

## Không làm

- New extractors or adapter modules under `src/`.
- Other stacks.
- Deep-support promotion.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
