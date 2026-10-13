---
key: TASK-RKG-055
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-043
status: in_progress
revision: 2
authorization: CR-RKG-037
change_set: CHG-RKG-2026-022
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
  context: CTX-TASK-RKG-055.yaml
  plan: PLAN-TASK-RKG-055.md
  diary: DIARY-TASK-RKG-055.md
  test: TEST-TASK-RKG-055-001.md
---
# TASK-RKG-055 — Static HTTP Callable to Endpoint link

Story: STORY-RKG-043. Pass `link_static_http_depends_on` đã có trên cây. Không phải adapter id. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-037 / CHG-RKG-2026-022. Không sửa `src/` trong lát hồ sơ này.

## Scope

Liên kết HTTP tĩnh sau merge: Callable `depends_on` đúng một Endpoint không phải navigation khi method và path tĩnh khớp một lần. Không thực thi source. Deep support withheld. Không phải adapter id.

## Ngoài phạm vi

Không sửa `builtin_adapters()`. Không target ExternalDependency. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-006.

AC-RKG-006. `tests/unit/test_http_depends.py` assert không tạo cạnh khi cặp method/path mơ hồ hoặc path động, và có diagnostic `http_depends_on_ambiguous` hoặc `http_depends_on_dynamic`.

## Chưa under test

AC-RKG-005 chưa under test. Suite assert `depends_on` Callable tới Endpoint. Then-clause đã xuất bản là Callable tới Callable hoặc Endpoint tới Callable. `OQ-RKG-008` mở trên `CHG-RKG-2026-022` và chặn đóng task này. Then-clause không sửa tại chỗ. AC-RKG-004, AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. Không có oracle census.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. Lát hồ sơ này chưa chạy pytest.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-055.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-055.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-055.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-055-001.md) — `not_run`
- [OQ-RKG-008](../change-sets/CHG-RKG-2026-022/open-questions/OQ-RKG-008.md)
