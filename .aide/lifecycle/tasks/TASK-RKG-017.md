---
uid: null
key: TASK-RKG-017
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-001
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 13
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  part_of:
  - EPIC-001-TEAM-RKG
  depends_on:
  - TASK-RKG-001
  implements:
  - FR-RKG-001
  - FR-RKG-002
  - FR-RKG-003
  - FR-RKG-004
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-017.yaml
  plan: PLAN-TASK-RKG-017.md
  diary: DIARY-TASK-RKG-017.md
---
# TASK-RKG-017 — MVP UI with mock client

Implement repository create/select onboarding, job states, Explorer,
evidence/dependency/technology panels and context export using contract-shaped
fixtures. Verify M0 portions of AC-RKG-011/018/027/043/054/056/057/061/066/068.

## Kết quả

- `frontend/`: shell, repositories (list/create/detail), job monitor, Explorer
  (`@xyflow/react`), panels, context export; mock `RkgClient` + demo fixture.
- Presentation tinh gọn hơn blueprint (panel collapsible, toolbar gọn); không sửa
  artifact thiết kế chuẩn tắc.
- Smoke: `DIARY-TASK-RKG-017`, `TEST-RKG-UI-MVP-MOCK-001` trên
  `frontend-mvp-mock-ui@09c7d74`.
- Còn lại ngoài scope: Ask UI (T-021), live client (T-024), repo/snapshot
  destructive guards đầy đủ (T-025).

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-017.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-017.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-017.md) — kết quả, evidence và các correction.
