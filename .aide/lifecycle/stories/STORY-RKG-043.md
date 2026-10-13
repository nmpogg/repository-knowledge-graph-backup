---
uid:
key: STORY-RKG-043
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-037
implementation_task: TASK-RKG-055
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-022
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-006]
classification: internal
ai_assisted: true
---
# STORY-RKG-043 — Static HTTP Callable to Endpoint link

## Giao cái gì

Pass `link_static_http_depends_on` đã có trên cây. Không phải adapter id. Liên kết HTTP tĩnh sau merge: Callable `depends_on` đúng một Endpoint không phải navigation khi method và path tĩnh khớp một lần. Không thực thi source. Deep support withheld. Không phải adapter id. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không sửa `builtin_adapters()`. Không target ExternalDependency. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-006. `tests/unit/test_http_depends.py` assert không tạo cạnh khi cặp method/path mơ hồ hoặc path động, và có diagnostic `http_depends_on_ambiguous` hoặc `http_depends_on_dynamic`.

## Chưa under test

AC-RKG-005 chưa under test. Suite assert `depends_on` Callable tới Endpoint. Then-clause đã xuất bản là Callable tới Callable hoặc Endpoint tới Callable. `OQ-RKG-008` mở và chặn đóng `TASK-RKG-055`. Then-clause không sửa tại chỗ. AC-RKG-004, AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. Không có oracle census.

## Task

- TASK-RKG-055 — Static HTTP Callable to Endpoint link
