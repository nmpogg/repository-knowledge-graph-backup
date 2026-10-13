---
uid:
key: STORY-RKG-041
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-035
implementation_task: TASK-RKG-053
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-020
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-006, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-041 — TanStack Router static navigation extraction

## Giao cái gì

Adapter `rkg.tanstack-router` đã có trên cây. Navigation TanStack Router tĩnh và `calls` khi `to` khớp đúng một route. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không HTTP method. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-006 và AC-RKG-048. `tests/conformance/test_tanstack_router_framework.py` assert navigation path, `handled_by`, `calls` `RKG.tanstack_router.navigate.v1`, và diagnostic không tạo cạnh khi đích động, binding bị che, route mơ hồ hoặc parent không resolve. Suite assert không có Endpoint HTTP method.

## Chưa under test

AC-RKG-004 chưa under test vì then-clause yêu cầu method; suite assert method vắng. AC-RKG-005, AC-RKG-007, AC-RKG-016 chưa under test. `evidence_ids` khác rỗng không assert rule_id và location của AC-RKG-007. Sentinel không nằm trong output không đủ để khai AC-RKG-016.

## Task

- TASK-RKG-053 — TanStack Router static navigation extraction
