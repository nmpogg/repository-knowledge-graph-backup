---
key: PLAN-TASK-RKG-043
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-043
revision: 1
plan_date: '2026-10-07'
change_set: CHG-RKG-2026-001
provenance: stack-b-normative-align
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
---

# PLAN-TASK-RKG-043 — Remaining verify only

Normative alignment for Stack B is settled. Remaining work is verification
evidence only — no new extractors.

OQ-RKG-007: assert `kind=navigation` + `framework_kind=nuxt` on page routes;
Nitro `server/api` HTTP Endpoints remain separate (method+path).

## Thứ tự

1. `conformance` — `pytest tests/conformance/test_vue_language.py -q`.
2. `conformance` — `pytest tests/conformance/test_nuxt_framework.py -q`.
3. `census` — `pytest tests/evaluation/test_nuxt_census.py -q`.
4. `evidence` — append test evidence under `evidence/tests/` linking results
   (relative paths only); do not erase prior reports.

## Không làm

- New extractors or adapter modules under `src/`.
- Deep-support promotion.
- React Router / BullMQ / Java / Go adapters.
- Live evaluation / Q&A / KPI.
- Mark task `done` or close gates.
