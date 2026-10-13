---
key: TASK-RKG-051
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-039
status: in_progress
revision: 3
authorization: CR-RKG-033
change_set: CHG-RKG-2026-018
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
  context: CTX-TASK-RKG-051.yaml
  plan: PLAN-TASK-RKG-051.md
  diary: DIARY-TASK-RKG-051.md
  test: TEST-TASK-RKG-051-001.md
---
# TASK-RKG-051 — Nest static route and message-pattern extraction

Story: STORY-RKG-039. Adapter `rkg.nest` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-033 / CHG-RKG-2026-018. Không sửa `src/` trong lát hồ sơ này.

## Scope

Route Nest tĩnh và message/event pattern tĩnh. Không thực thi source. Deep support withheld. `publishes` không thuộc phần suite đang assert.

## Ngoài phạm vi

Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-004, AC-RKG-006, AC-RKG-007, AC-RKG-015.

AC-RKG-006 và AC-RKG-015. `tests/conformance/test_nest_framework.py` assert HTTP method và path, MessageChannel kind cùng `consumes`, và diagnostic không tạo cạnh khi prefix hoặc pattern động. Không assert `publishes`.

## Chưa under test

AC-RKG-004 `handled_by` và AC-RKG-007 rule id cùng evidence location đã có assert (`TEST-RKG-AC007-ASSERT-001`, passed). AC-RKG-005, AC-RKG-016, AC-RKG-048 chưa under test. Sentinel không nằm trong repr không đủ để khai AC-RKG-016. Status stays `in_progress`.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. TEST-RKG-AC007-ASSERT-001 ghi passed cho assert rule id và evidence location. Census trong plan không nằm trong lần chạy đó. Task chưa done.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-051.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-051.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-051.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-051-001.md) — ot_run