---
key: TASK-RKG-053
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-041
status: in_progress
revision: 3
authorization: CR-RKG-035
change_set: CHG-RKG-2026-020
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
  context: CTX-TASK-RKG-053.yaml
  plan: PLAN-TASK-RKG-053.md
  diary: DIARY-TASK-RKG-053.md
  test: TEST-TASK-RKG-053-001.md
---
# TASK-RKG-053 — TanStack Router static navigation extraction

Story: STORY-RKG-041. Adapter `rkg.tanstack-router` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-035 / CHG-RKG-2026-020. Không sửa `src/` trong lát hồ sơ này.

## Scope

Navigation TanStack Router tĩnh và `calls` khi `to` khớp đúng một route. Không thực thi source. Deep support withheld.

## Ngoài phạm vi

Không HTTP method. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-006, AC-RKG-007, AC-RKG-048.

AC-RKG-006 và AC-RKG-048. `tests/conformance/test_tanstack_router_framework.py` assert navigation path, `handled_by`, `calls` `RKG.tanstack_router.navigate.v1`, và diagnostic không tạo cạnh khi đích động, binding bị che, route mơ hồ hoặc parent không resolve. Suite assert không có Endpoint HTTP method.

## Chưa under test

AC-RKG-007 đã có assert rule id và evidence location (`TEST-RKG-AC007-ASSERT-001`, passed). AC-RKG-004 chưa under test vì then-clause yêu cầu method; suite assert method vắng. AC-RKG-005, AC-RKG-016 chưa under test. Sentinel không nằm trong output không đủ để khai AC-RKG-016. Status stays `in_progress`.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. TEST-RKG-AC007-ASSERT-001 ghi passed cho assert rule id và evidence location. Census trong plan không nằm trong lần chạy đó. Task chưa done.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-053.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-053.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-053.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-053-001.md) — ot_run