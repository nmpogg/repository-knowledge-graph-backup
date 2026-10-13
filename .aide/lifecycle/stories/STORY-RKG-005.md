---
uid:
key: STORY-RKG-005
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: done
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-022, AC-RKG-020, AC-RKG-021, AC-RKG-040, AC-RKG-052, AC-RKG-053, AC-RKG-065]
classification: internal
ai_assisted: true
---
# STORY-RKG-005 — Inventory dependency và chọn adapter

## Giao cái gì

Đọc manifest dependency thành ExternalDependency với provenance version, không suy version từ máy analyzer. Detection công bố support state và không nhận nhầm thư viện bị shadow. Nhiều adapter hợp lệ cùng chạy. Nhiều application entrypoint thì dừng để người dùng chọn; đúng một entrypoint thì tự chọn; framework bắt buộc entrypoint mà không resolve được thì job failed.

## Ngoài phạm vi

Không implement từng deep adapter (STORY-RKG-006). UI chọn app thuộc STORY-RKG-001.

## Task

- TASK-RKG-007 — Python metadata adapter and package inventory
- TASK-RKG-008 — Technology detection and adapter selection
