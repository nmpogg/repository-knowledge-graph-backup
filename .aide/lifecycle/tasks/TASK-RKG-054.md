---
key: TASK-RKG-054
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-042
status: in_progress
revision: 2
authorization: CR-RKG-036
change_set: CHG-RKG-2026-021
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-054.yaml
  plan: PLAN-TASK-RKG-054.md
  diary: DIARY-TASK-RKG-054.md
  test: TEST-TASK-RKG-054-001.md
---
# TASK-RKG-054 — Vue Router static navigation extraction

Story: STORY-RKG-042. Adapter `rkg.vue-router` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-036 / CHG-RKG-2026-021. Không sửa `src/` trong lát hồ sơ này.

## Scope

Navigation Vue Router tĩnh và `calls` khi đích khớp đúng một route. Không thực thi source. Deep support withheld.

## Ngoài phạm vi

Không HTTP method. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-006, AC-RKG-048.

AC-RKG-006 và AC-RKG-048. `tests/conformance/test_vue_router_framework.py` assert navigation path, `handled_by` tới `setup`, `calls` `RKG.vue_router.navigate.v1`, và diagnostic `vue_router_navigate_dynamic` không tạo cạnh.

## Chưa under test

AC-RKG-004 chưa under test: suite assert path và `handled_by`, không assert HTTP method. AC-RKG-005, AC-RKG-007, AC-RKG-016 chưa under test. Khớp rule trên evidence của cạnh navigate không assert mọi edge có location hợp lệ. Sentinel không nằm trong diagnostic không đủ để khai AC-RKG-016.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. Lát hồ sơ này chưa chạy pytest.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-054.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-054.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-054.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-054-001.md) — ot_run