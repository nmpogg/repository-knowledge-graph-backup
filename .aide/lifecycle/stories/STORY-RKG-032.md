---
key: STORY-RKG-032
group: normative
scope: lifecycle
system: SYS-RKG
revision: 2
authorization: CR-RKG-020
verification_evidence: TEST-TASK-RKG-038-003
review_record: REV-TASK-RKG-038-002
change_set: CHG-RKG-2026-005
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
implementation_task: TASK-RKG-038
phase: implementation_verified_independently_reviewed_pending_gate_decision
---
# STORY-RKG-032 — Chẩn đoán lượt hỏng và làm rõ câu trả lời thất bại

## Giao cái gì

Giữ từ chối output không hợp lệ và trạng thái đã commit an toàn. Đưa neo endpoint, giới hạn path và ngữ nghĩa sentinel của planner vào hướng dẫn model. Chẩn đoán theo stage/reason đã allowlist, không đưa prompt, response hay giá trị cấu hình. Lượt failed, interrupted hoặc pending không hiện ghi chú coverage/limit và được giải thích tự nhiên.

## Ngoài phạm vi

Không suy nguyên nhân sự cố sống từ thông báo lỗi chung. Không đổi schema gốc, grounding, idempotency hay mặc định không trần.

## Task

- TASK-RKG-038
