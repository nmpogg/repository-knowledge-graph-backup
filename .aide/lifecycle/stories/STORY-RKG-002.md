---
uid:
key: STORY-RKG-002
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-001-TEAM-RKG
status: done
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-001-TEAM-RKG]
satisfies: [AC-RKG-054, AC-RKG-066, AC-RKG-067, AC-RKG-068, AC-RKG-069, AC-RKG-070, AC-RKG-071, AC-RKG-072]
classification: internal
ai_assisted: true
---
# STORY-RKG-002 — Quản lý repository và snapshot trên mock

## Giao cái gì

Lát cắt UI quản lý catalog: tạo, sửa, xem, xóa repository và liệt kê, kích hoạt, xóa snapshot trên mock cùng contract. Có revision conflict, confirm trước thao tác phá hủy, empty/error, và bàn giao sang Explorer sau activate. Phần UI của các AC này được chốt ở đây trước khi có API.

## Ngoài phạm vi

Không persist catalog và không publish snapshot thật (STORY-RKG-007, STORY-RKG-010). Live client thuộc STORY-RKG-011.

## Task

- TASK-RKG-025 — Repository and snapshot management UI (mock)
