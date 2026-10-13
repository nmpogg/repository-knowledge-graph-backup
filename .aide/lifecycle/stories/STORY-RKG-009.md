---
uid:
key: STORY-RKG-009
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
satisfies: [AC-RKG-034, AC-RKG-055, AC-RKG-012, AC-RKG-038]
classification: internal
ai_assisted: true
---
# STORY-RKG-009 — Điều phối index job và CLI

## Giao cái gì

Một job thuộc một repository, serialize toàn ứng dụng, phục hồi job bị ngắt, và xuất scan report đủ tổng. CLI `index` và `serve` dùng cùng validation với API. `serve` bind loopback, một worker. Parse lỗi từng file mà candidate còn hợp lệ thì `succeeded_with_warnings`, không phát minh trạng thái `partial`.

## Ngoài phạm vi

Benchmark wall time AC-RKG-039 thuộc STORY-RKG-015. Endpoint HTTP thuộc STORY-RKG-010.

## Task

- TASK-RKG-015 — Index job coordinator and CLI
