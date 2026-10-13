---
key: STORY-RKG-034
group: normative
scope: lifecycle
system: SYS-RKG
revision: 2
authorization: CR-RKG-022
verification_evidence: TEST-TASK-RKG-040-002
review_record: REV-TASK-RKG-040-001
change_set: CHG-RKG-2026-007
classification: internal
ai_assisted: true
type: story
epic: EPIC-006-TEAM-RKG
status: in_progress
satisfies:
- AC-RKG-074
- AC-RKG-080
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
implementation_task: TASK-RKG-040
phase: implementation_verified_independently_reviewed_pending_gate_decision
---
# STORY-RKG-034 — Đường dẫn narrative graph hợp lệ

## Giao cái gì

Sửa sinh đường dẫn bị ngắt bằng hướng dẫn model có witness đường đi đã chứng minh trên graph. Giữ kiểm tra output nghiêm ngặt cho cả câu trả lời, citation và trạng thái.

## Ngoài phạm vi

Không nới validation để chấp nhận đường đi không chứng minh được. Không suy release readiness khi Component Merge Gate còn pending.

## Task

- TASK-RKG-040
