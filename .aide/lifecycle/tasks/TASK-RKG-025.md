---
uid: null
key: TASK-RKG-025
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-002
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 10
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  part_of:
  - EPIC-001-TEAM-RKG
  depends_on:
  - TASK-RKG-001
  - TASK-RKG-017
  implements:
  - FR-RKG-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-025.yaml
  plan: PLAN-TASK-RKG-025.md
  diary: DIARY-TASK-RKG-025.md
---
# TASK-RKG-025 — Repository and snapshot management UI (mock)

Implement repository list/create/edit/detail/delete và snapshot
list/detail/activate/delete bằng contract-shaped mock, gồm optimistic conflict,
empty/error/confirm/blocked states và Explorer handoff. Verify phần UI của
AC-RKG-066…072 trên fixture mock; không đánh `done` khi chưa có evidence smoke cho
create → index result → activate → Explorer và destructive guards.

## Hoàn tất

Evidence: `DIARY-TASK-RKG-025`, `TEST-RKG-UI-REPO-MGMT-MOCK-001` (lint/test/build
pass trên mock; create → index → activate → Explorer + delete guards). Blueprint
`SCR-RKG-001` / `UIS-RKG-001`. Live API thuộc `TASK-RKG-024`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-025.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-025.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-025.md) — kết quả, evidence và các correction.
