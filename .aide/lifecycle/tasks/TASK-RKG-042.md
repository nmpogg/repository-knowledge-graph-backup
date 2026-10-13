---
key: TASK-RKG-042
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-026
status: in_progress
revision: 3
authorization: CR-RKG-024
change_set: CHG-RKG-2026-009
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-004
  - TASK-RKG-005
  - TASK-RKG-006
  - TASK-RKG-009
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-042.yaml
  plan: PLAN-TASK-RKG-042.md
  diary: DIARY-TASK-RKG-042.md
---
# TASK-RKG-042 — TypeScript language + React Router adapters

Adapters `rkg.typescript` (language) and `rkg.react-router` (framework) are
implemented and registered. Oracle: `repo-test/rkg-fixture-react-ts`. Remaining
work is verify (conformance + react-ts census) and deep-support review — not
closed. Task stays `in_progress` until verify + evidence.

## Scope

- Language: imports (named/default/namespace/alias, relative `../`, path alias
  `@/`), call chain `OrdersPage → useOrders → orderApi.listOrders → httpClient.get`,
  configuration keys `VITE_API_BASE_URL` / `VITE_ENABLE_ADMIN`, literal external
  origin `https://inventory.example.test`, syntax-error isolation, no-guess
  negatives (AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048).
- Framework: static React Router paths as `Endpoint` with `kind=navigation`,
  `framework_kind=react-router`, no HTTP method, no repository `exposes`
  (OQ-RKG-007 resolved). Dynamic/conditional route → diagnostic.
- Out of scope this task: new extractor work; deep-supported promotion; Nuxt,
  BullMQ, Java, Go; live eval/KPI; full golden index of the fixture (PLAN
  follow-up).

## Acceptance criteria under test

AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048. Verify path:
conformance suites and react-ts census. Append evidence
(`DIARY-TASK-RKG-042-r2` and later) before marking done.

## Result

Verify lát recorded: `TEST-RKG-TYPESCRIPT-REACT-ROUTER-001` (14 + 2 pytest
passed on commit `2d0af72…`) and `DIARY-TASK-RKG-042-r4`. Status remains
`in_progress` — deep-support review not closed.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-042.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-042.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-042.md)
- [Verify evidence](../../evidence/tests/TEST-RKG-TYPESCRIPT-REACT-ROUTER-001.md)
