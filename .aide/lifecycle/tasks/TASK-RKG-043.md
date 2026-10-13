---
key: TASK-RKG-043
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-027
status: in_progress
revision: 5
authorization: CR-RKG-025
change_set: CHG-RKG-2026-010
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
  context: CTX-TASK-RKG-043.yaml
  plan: PLAN-TASK-RKG-043.md
  diary: DIARY-TASK-RKG-043.md
---
# TASK-RKG-043 — Vue language + Nuxt framework adapters

Story: STORY-RKG-027. Adapters `rkg.vue` (language) and `rkg.nuxt` (framework)
are implemented and registered. Oracle: `repo-test/rkg-fixture-nuxt4`. Remaining
work is verify (conformance `test_vue_language.py` / `test_nuxt_framework.py` +
`test_nuxt_census.py`) and deep-support review — not closed. Task stays
`in_progress` until verify + evidence.

## Scope

- Language (`rkg.vue`): Vue SFC structure (template/script/style as sections on
  one SourceUnit), imports (relative `.vue` targets), calls (unique same-SFC),
  syntax-error isolation with relative path, no-guess negatives
  (AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048).
- Framework (`rkg.nuxt`): Nuxt pages as `Endpoint` with `kind=navigation`,
  `framework_kind=nuxt`, no HTTP method, no repository `exposes`
  (OQ-RKG-007 resolved); Nitro `server/api` HTTP Endpoints (method+path);
  `runtimeConfig` / `runtimeDefaults` keys as Configuration; server/composable
  `.ts` reuse `rkg.typescript` (TASK-RKG-042).
- Out of scope this task: new extractors; deep-supported promotion; BullMQ,
  React Router, Java, Go; live eval/KPI.

## Acceptance criteria under test

AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048. Framework
route/HTTP patterns as covered by Nuxt conformance. Verify path: conformance
suites and nuxt census. Append evidence before marking done.

## Result

Verify lát recorded: `TEST-RKG-VUE-NUXT-001` (14 + 2 pytest passed on commit
`2d0af72…`) and `DIARY-TASK-RKG-043-r2`. Status remains `in_progress` —
deep-support review not closed.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-043.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-043.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-043.md)
- [Verify evidence](../../evidence/tests/TEST-RKG-VUE-NUXT-001.md)
