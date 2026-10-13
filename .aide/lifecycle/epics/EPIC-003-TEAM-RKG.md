---
uid: null
key: EPIC-003-TEAM-RKG
type: epic
group: normative
scope: lifecycle
system: SYS-RKG
status: done
revision: 10
change_set: CHG-RKG-2026-001
implements:
- FR-RKG-001
- FR-RKG-003
affected_components:
- CMP-RKG-WEB
- CMP-RKG-TRANSPORT
- CMP-RKG-GRAPH
contracts:
  produces: []
  consumes:
  - API-RKG-CORE-v1
blocked_by: []
ready_criteria:
- contract_frozen
- context_valid
- tests_green
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  part_of:
  - CHG-RKG-2026-001
classification: internal
ai_assisted: true
---
# EPIC-003-TEAM-RKG — M3 Explorer tích hợp

Thay mock client bằng API thật mà không viết lại screen behavior đã nghiệm thu ở M0.

## Phạm vi

Một team. Nối UI đã duyệt vào API thật, rồi thêm Structure và luồng graph tập trung. Không có epic team khác để `blocked_by`.

## Story

- STORY-RKG-011 — Explorer và quản lý repository trên API thật
- STORY-RKG-019 — Luồng graph tập trung theo entity gốc

## Done when

`TASK-RKG-024`, `TASK-RKG-026` và `TASK-RKG-029` hoàn tất. AC-RKG-011/018/027/043/
054/056/057/061/066…072 chạy với backend thật. Structure control thuộc TASK-RKG-026 trực tiếp Epic; current `AC-RKG-073` thuộc STORY-RKG-017. Focused flow thuộc
STORY-RKG-019 và không bao gồm AC-RKG-073. Cả hai có evidence trên client đã
nối API. Mock/live không lệch schema, state hoặc accessibility behavior. Status
epic là `done` vì `TASK-RKG-024`, `TASK-RKG-026` và `TASK-RKG-029` đã `done`.
Gate vẫn pending. Revision 6 gộp AC-RKG-073 vào dòng Structure của epic này.

## Task trực tiếp Epic

- TASK-RKG-026 — Historical Structure view (no separate current AC).
