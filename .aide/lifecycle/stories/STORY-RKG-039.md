---
uid:
key: STORY-RKG-039
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-033
implementation_task: TASK-RKG-051
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-018
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-006, AC-RKG-015]
classification: internal
ai_assisted: true
---
# STORY-RKG-039 — Nest static route and message-pattern extraction

## Giao cái gì

Adapter `rkg.nest` đã có trên cây. Route Nest tĩnh và message/event pattern tĩnh. Không thực thi source. Deep support withheld. `publishes` không thuộc phần suite đang assert. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-006 và AC-RKG-015. `tests/conformance/test_nest_framework.py` assert HTTP method và path, MessageChannel kind cùng `consumes`, và diagnostic không tạo cạnh khi prefix hoặc pattern động. Không assert `publishes`.

## Chưa under test

AC-RKG-004 chưa under test: suite assert method và path, không assert `handled_by`. AC-RKG-005, AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. Sentinel không nằm trong repr không đủ để khai AC-RKG-016.

## Task

- TASK-RKG-051 — Nest static route and message-pattern extraction
