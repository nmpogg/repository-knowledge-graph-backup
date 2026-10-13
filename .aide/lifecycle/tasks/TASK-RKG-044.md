---
key: TASK-RKG-044
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-028
status: in_progress
revision: 6
authorization: CR-RKG-026
change_set: CHG-RKG-2026-011
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-004
  - TASK-RKG-042
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-044.yaml
  plan: PLAN-TASK-RKG-044.md
  diary: DIARY-TASK-RKG-044.md
---
# TASK-RKG-044 — BullMQ messaging adapter

Story: STORY-RKG-028. Adapter `rkg.bullmq` (messaging) is implemented and
registered. Depends on `rkg.typescript` (TASK-RKG-042). Oracle:
`repo-test/rkg-fixture-bullmq-worker`. Remaining work is verify via
`tests/evaluation/test_bullmq_census.py` (census-focused; no separate BullMQ
conformance suite in tree) and deep-support review — not closed. Task stays
`in_progress` until verify + evidence.

## Scope

- Messaging (`rkg.bullmq`): Queue/Worker constructors → `MessageChannel`
  `channel_kind=queue`; Worker in callable → `consumes`; resolved `queue.add`
  → `publishes`; no Redis URL/connection or payload in graph; no HTTP
  `Endpoint` for job schedulers / repeatables; deep-support open
  (AC-RKG-015, AC-RKG-006, AC-RKG-007).
- Out of scope this task: new extractors; Vue/Nuxt/React Router/Java/Go;
  deep-supported promotion; live eval/KPI.

## Acceptance criteria under test

AC-RKG-015, AC-RKG-006, AC-RKG-007. Verify path: bullmq census
(`test_bullmq_census.py` / `expected_bullmq.json`). Append evidence before
marking done.

## Result

Verify lát recorded: `TEST-RKG-BULLMQ-001` (2 pytest passed on commit
`2d0af72…`) and `DIARY-TASK-RKG-044-r2`. Status remains `in_progress` —
deep-support review not closed; census-only path (no BullMQ conformance suite).

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-044.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-044.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-044.md)
- [Verify evidence](../../evidence/tests/TEST-RKG-BULLMQ-001.md)
