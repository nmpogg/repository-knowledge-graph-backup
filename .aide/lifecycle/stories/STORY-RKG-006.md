---
uid:
key: STORY-RKG-006
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
satisfies: [AC-RKG-004, AC-RKG-005, AC-RKG-013, AC-RKG-014, AC-RKG-015, AC-RKG-016, AC-RKG-023]
classification: internal
ai_assisted: true
---
# STORY-RKG-006 — Trích xuất FastAPI, SQLAlchemy, messaging và config

## Giao cái gì

Bốn deep adapter của MVP, chạy trên parsed unit của language adapter: endpoint và dependency wiring, DataResource cùng reads/writes, MessageChannel, configuration key và HTTP origin literal. Pattern không đủ bằng chứng thành diagnostic. Secret sentinel không vào graph, report hay context.

## Ngoài phạm vi

Các lỗ static FastAPI phát hiện sau pilot (factory cục bộ, vòng lặp literal, path rỗng, version chưa xác minh) thuộc STORY-RKG-018. Không publish snapshot.

## Task

- TASK-RKG-009 — FastAPI framework adapter
- TASK-RKG-010 — SQLAlchemy 2.x data-access adapter
- TASK-RKG-011 — aiokafka messaging adapter
- TASK-RKG-012 — Configuration and HTTP dependency extraction
