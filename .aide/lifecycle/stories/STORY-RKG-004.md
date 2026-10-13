---
uid:
key: STORY-RKG-004
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: done
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-035, AC-RKG-006, AC-RKG-048, AC-RKG-017, AC-RKG-007]
classification: internal
ai_assisted: true
---
# STORY-RKG-004 — Cấu trúc Python, import, lời gọi và quan hệ class

## Giao cái gì

Language adapter Python 3.12 đọc manifest thành SourceUnit, type, callable và quan hệ import/call/inherit/implement có evidence. File không parse được thành diagnostic. Target mơ hồ không sinh cạnh đoán. Validator từ chối edge thiếu evidence hoặc lệch snapshot.

## Ngoài phạm vi

Snapshot lúc lát cắt này còn dùng Namespace cho scope module, đúng golden fixture đã giao ở TASK-RKG-002. Directory và bỏ Namespace trên snapshot mới là STORY-RKG-017, sau ADR-2026-006. Không extract route, bảng hay topic.

## Task

- TASK-RKG-005 — Python language adapter: AST and lexical scope
- TASK-RKG-006 — Python adapter import, call and class resolution

## Revision 2

Revision 1 listed `AC-RKG-002` and `AC-RKG-003`. Current text of those AC is the
Directory-era contract: no new Namespace nodes, and Directory is not an import
target. That behavior is satisfied by `STORY-RKG-017`. This story does not list
them. The tasks above remain the historical Python slice.
