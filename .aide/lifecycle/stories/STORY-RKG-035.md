---
key: STORY-RKG-035
group: normative
scope: lifecycle
system: SYS-RKG
revision: 2
authorization: CR-RKG-023
verification_evidence: TEST-TASK-RKG-041-003
review_record: REV-TASK-RKG-041-002
change_set: CHG-RKG-2026-008
classification: internal
ai_assisted: true
type: story
epic: EPIC-006-TEAM-RKG
status: in_progress
satisfies:
- AC-RKG-074
- AC-RKG-075
- AC-RKG-080
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
implementation_task: TASK-RKG-041
phase: implementation_verified_independently_reviewed_pending_gate_decision
---
# STORY-RKG-035 — Câu hỏi thực thể và vị trí nguồn tự nhiên

## Giao cái gì

Luồng câu hỏi người dùng đầy đủ khi chưa chọn sẵn root: gọi logout bằng ngôn ngữ tự nhiên và hỏi vị trí nguồn. Giữ fact đã ghim, validation nghiêm và làm rõ khi còn mơ hồ, gồm thứ tự tên thực thể và đại từ.

## Ngoài phạm vi

Không coi test đã chọn root là đủ cho luồng này. Không đổi provider đang giữ OpenAI-only.

## Task

- TASK-RKG-041
