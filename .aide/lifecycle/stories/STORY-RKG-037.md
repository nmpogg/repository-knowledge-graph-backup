---
uid:
key: STORY-RKG-037
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-031
implementation_task: TASK-RKG-049
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-016
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-006, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-037 — Next static route and navigation extraction

## Giao cái gì

Adapter `rkg.next` đã có trên cây. Route Next tĩnh (page, route handler, pages API có verb literal) và navigation `calls` khi target resolve đúng một route. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-004, AC-RKG-006 và AC-RKG-048. `tests/conformance/test_next_framework.py` assert HTTP method và path, navigation path, `handled_by`, `calls` `RKG.next.navigation.v1` kèm evidence id, và diagnostic không tạo cạnh cho href động, binding bị che, route mơ hồ, handler chưa resolve.

## Chưa under test

AC-RKG-003, AC-RKG-005, AC-RKG-007, AC-RKG-016, AC-RKG-035 chưa under test. Suite assert không có cạnh `depends_on` tới Endpoint trong các case đó. Sentinel không nằm trong output không đủ để khai AC-RKG-016. `evidence_ids` khác rỗng không assert rule_id và location của AC-RKG-007.

## Task

- TASK-RKG-049 — Next static route and navigation extraction
