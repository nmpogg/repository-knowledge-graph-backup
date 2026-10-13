---
key: PLAN-TASK-RKG-042-r2
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-042
revision: 1
plan_date: '2026-10-07'
change_set: CHG-RKG-2026-001
provenance: stack-a-normative-align
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  prior_plan: PLAN-TASK-RKG-042.md
---

# PLAN-TASK-RKG-042-r2 — Remaining verify only

Normative alignment for Stack A is settled. Remaining work is verification
evidence only — no new extractors.

OQ-RKG-007 resolved: assert `kind=navigation` + `framework_kind=react-router`
(not provisional).

## Thứ tự

1. `conformance` — `pytest tests/conformance/test_typescript_language.py`
   `tests/conformance/test_react_router_framework.py -q`.
2. `census` — `pytest tests/evaluation/test_react_ts_census.py -q`.
3. `evidence` — append test evidence under `evidence/tests/` linking results
   (relative paths only); do not erase prior reports.

## Không làm

- New extractors or adapter modules under `src/`.
- Deep-support promotion.
- Nuxt / BullMQ / Java / Go adapters.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
