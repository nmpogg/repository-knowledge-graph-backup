---
uid:
key: STORY-RKG-027
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-025
implementation_task: TASK-RKG-043
verification_evidence: TEST-RKG-VUE-NUXT-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-010
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-027 — Vue language + Nuxt framework extraction

## Giao cái gì

Language adapter `rkg.vue` và framework adapter `rkg.nuxt` trên oracle fixture
`repo-test/rkg-fixture-nuxt4`: cấu trúc SFC (template/script/style), import,
call. Nuxt pages thành `Endpoint` với `kind=navigation`, `framework_kind=nuxt`,
không HTTP method, không repository `exposes` (OQ-RKG-007 đã resolve). Nitro
`server/api` thành HTTP Endpoint (method+path). `runtimeConfig` /
`runtimeDefaults` keys thành Configuration. Server/composable TypeScript tái
dụng `rkg.typescript`.

## Ngoài phạm vi

Không đóng deep-support review. Không BullMQ/React Router/Java/Go. Không live
eval/KPI. Không deep set Python MVP.

## AC đang kiểm

AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048 qua
`test_vue_language.py`, `test_nuxt_framework.py` và `test_nuxt_census.py`.
Server và composable TypeScript dùng lại `rkg.typescript` của TASK-RKG-042.

## Hiện trạng

`TEST-RKG-VUE-NUXT-001` ghi 14 + 2 pytest đã qua.
`REV-RKG-STACK-SUPPORT-001` ghi `test_nuxt_framework.py` chưa assert
`exposes==[]`, nên deep-supported vẫn đóng. Story ở `in_progress`.

## Task

- TASK-RKG-043 — Vue language + Nuxt framework adapters

## Note on AC-RKG-003

FR lists `story: [STORY-RKG-017]` on AC-RKG-003 for Directory-era import contract
ownership. This story verifies the same language-agnostic AC on the Vue/Nuxt
fixture. Do not remove AC-003 from STORY-RKG-017 or edit FR.
