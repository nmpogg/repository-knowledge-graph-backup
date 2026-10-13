---
key: PLAN-TASK-RKG-045
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-045
revision: 1
plan_date: '2026-10-08'
change_set: CHG-RKG-2026-001
provenance: stack-d-normative-align
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
---

# PLAN-TASK-RKG-045 — Remaining verify only

Normative alignment for Stack D is settled. Remaining work is verification
evidence only — no new extractors.

## Thứ tự

1. `java-language` — `pytest tests/conformance/test_java_language.py -q`.
2. `spring-stack` — `pytest tests/conformance/test_spring_stack.py -q`.
3. `spring-census` — `pytest tests/evaluation/test_spring_census.py -q`.
4. `evidence` — append test evidence under `evidence/tests/` linking results
   (relative paths only); do not erase prior reports.

## Không làm

- New extractors or adapter modules under `src/`.
- TypeScript/Vue/BullMQ/Go adapters.
- Deep-support promotion.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
