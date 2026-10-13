---
uid:
key: STORY-RKG-008
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
satisfies: [AC-RKG-009, AC-RKG-036, AC-RKG-060, AC-RKG-010]
classification: internal
ai_assisted: true
---
# STORY-RKG-008 — Tìm kiếm, duyệt graph và bounded context

## Giao cái gì

Đọc snapshot đã publish: search có thứ tự ổn định, traversal hữu hạn theo hướng và loại cạnh, và context JSON lặp lại được trong budget. Không có active snapshot, snapshot unavailable, hoặc identity lệch repository thì từ chối, không trả graph rỗng giả.

## Ngoài phạm vi

Ngưỡng p95 của AC-RKG-037 và AC-RKG-062 đo ở STORY-RKG-015. Luồng tập trung theo entity gốc thuộc STORY-RKG-019. HTTP wrapper thuộc STORY-RKG-010.

## Task

- TASK-RKG-014 — Search, traversal and context services
