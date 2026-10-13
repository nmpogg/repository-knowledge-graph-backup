---
uid:
key: STORY-RKG-026
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-024
implementation_task: TASK-RKG-042
verification_evidence: TEST-RKG-TYPESCRIPT-REACT-ROUTER-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-009
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-026 — TypeScript language + React Router framework extraction

## Giao cái gì

Language adapter `rkg.typescript` và framework adapter `rkg.react-router` trên
oracle fixture `repo-test/rkg-fixture-react-ts`: import, call chain, configuration
key, external origin literal, syntax-error isolation và no-guess negatives.
Static React Router paths thành `Endpoint` với `kind=navigation`,
`framework_kind=react-router`, không HTTP method, không repository `exposes`
(OQ-RKG-007 đã resolve).

## Ngoài phạm vi

Không đóng deep-support review. Không Nuxt/BullMQ/Java/Go. Không live eval/KPI.
Không full golden index của fixture (follow-up). Không deep set Python MVP.

## AC đang kiểm

AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048 qua conformance
TypeScript/React Router và census react-ts. Route tĩnh thành `Endpoint`
`kind=navigation`, `framework_kind=react-router`, không HTTP method, không
repository `exposes`.

## Hiện trạng

`TEST-RKG-TYPESCRIPT-REACT-ROUTER-001` ghi 14 + 2 pytest đã qua.
`REV-RKG-STACK-SUPPORT-001` không ghi pass rate
`TEST-RKG-ADAPTER-CONFORMANCE` và không thăng deep-supported. Story ở
`in_progress`.

## Task

- TASK-RKG-042 — TypeScript language + React Router adapters

## Note on AC-RKG-003

FR lists `story: [STORY-RKG-017]` on AC-RKG-003 for Directory-era import contract
ownership. This story verifies the same language-agnostic AC on the TypeScript
fixture. Do not remove AC-003 from STORY-RKG-017 or edit FR.
