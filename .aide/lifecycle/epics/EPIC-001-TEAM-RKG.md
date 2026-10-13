---
uid:
key: EPIC-001-TEAM-RKG
type: epic
group: normative
scope: lifecycle
system: SYS-RKG
status: done
revision: 8
change_set: CHG-RKG-2026-001
implements: [FR-RKG-001, FR-RKG-003]
affected_components: [CMP-RKG-WEB]
contracts: { produces: [], consumes: [API-RKG-CORE-v1] }
blocked_by: []
ready_criteria: [contract_frozen, context_valid, tests_green]
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {part_of: [CHG-RKG-2026-001]}
classification: internal
ai_assisted: true
---
# EPIC-001-TEAM-RKG — M0 MVP giao diện

Khung dự án và luồng UI end-to-end dùng mock client/fixture có cùng contract API.

## Phạm vi

Một team. Giao toolchain và hai lát cắt UI trên mock, trước khi backend publish snapshot. Không chờ epic của team khác.

## Story

- STORY-RKG-001 — Onboarding, theo dõi job và Explorer trên mock
- STORY-RKG-002 — Quản lý repository và snapshot trên mock

## Task (không qua Story — không có AC)

- TASK-RKG-001 — Project skeleton and toolchain

## Done when

`TASK-RKG-001`, `TASK-RKG-017` và `TASK-RKG-025` hoàn tất; mock responses khớp API
v1; repository create/management, snapshot lifecycle, onboarding, job, Explorer,
evidence và context export đạt phần M0 của AC-RKG-011/018/027/043/054/056/057/
061/066…072.

## Tiến độ (2026-09-24)

Ba task điều kiện trên đã `done` với evidence:
`DIARY-TASK-RKG-001*` / `TEST-RKG-DDL-BOOTSTRAP-001`,
`DIARY-TASK-RKG-017` / `TEST-RKG-UI-MVP-MOCK-001`,
`DIARY-TASK-RKG-025` / `TEST-RKG-UI-REPO-MGMT-MOCK-001`.
Status epic là `done` vì `TASK-RKG-001`, `TASK-RKG-017` và `TASK-RKG-025` đã `done`. Gate và baseline M0 không được ký bởi câu này.
