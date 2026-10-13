---
uid:
key: STORY-RKG-040
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-034
implementation_task: TASK-RKG-052
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-019
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-006]
classification: internal
ai_assisted: true
---
# STORY-RKG-040 — Go HTTP static route extraction

## Giao cái gì

Adapter `rkg.go-http` đã có trên cây. Route Gin, chi và gorilla/mux tĩnh thành Endpoint method và path, với `handled_by` khi handler resolve một Callable. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không thêm fact vào fixture event-worker. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-004 và AC-RKG-006. `tests/conformance/test_go_http_framework.py` assert method, path, `handled_by` khi handler resolve một lần, diagnostic cho path động và handler bị che hoặc trùng tên, và không có cạnh `depends_on`.

## Chưa under test

AC-RKG-005 chưa under test: suite assert vắng `depends_on`, không assert chiều depends_on của AC. AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. Sentinel không nằm trong output không đủ để khai AC-RKG-016.

## Task

- TASK-RKG-052 — Go HTTP static route extraction
