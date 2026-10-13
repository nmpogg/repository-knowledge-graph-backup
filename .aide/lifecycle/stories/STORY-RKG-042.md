---
uid:
key: STORY-RKG-042
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-036
implementation_task: TASK-RKG-054
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-021
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-006, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-042 — Vue Router static navigation extraction

## Giao cái gì

Adapter `rkg.vue-router` đã có trên cây. Navigation Vue Router tĩnh và `calls` khi đích khớp đúng một route. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không HTTP method. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-006 và AC-RKG-048. `tests/conformance/test_vue_router_framework.py` assert navigation path, `handled_by` tới `setup`, `calls` `RKG.vue_router.navigate.v1`, và diagnostic `vue_router_navigate_dynamic` không tạo cạnh.

## Chưa under test

AC-RKG-004 chưa under test: suite assert path và `handled_by`, không assert HTTP method. AC-RKG-005, AC-RKG-007, AC-RKG-016 chưa under test. Khớp rule trên evidence của cạnh navigate không assert mọi edge có location hợp lệ. Sentinel không nằm trong diagnostic không đủ để khai AC-RKG-016.

## Task

- TASK-RKG-054 — Vue Router static navigation extraction
