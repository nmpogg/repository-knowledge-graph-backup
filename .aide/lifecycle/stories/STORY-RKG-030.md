---
key: STORY-RKG-030
group: normative
scope: lifecycle
system: SYS-RKG
revision: 3
authorization: CR-RKG-018
verification_evidence: TEST-TASK-RKG-036-003
review_record: REV-TASK-RKG-036-002
change_set: CHG-RKG-2026-003
classification: internal
ai_assisted: true
type: story
epic: EPIC-006-TEAM-RKG
status: done
satisfies:
- AC-RKG-074
- AC-RKG-077
- AC-RKG-078
- AC-RKG-080
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
implementation_task: TASK-RKG-036
phase: implementation_verified_independently_reviewed_pending_gate_decision
---
# STORY-RKG-030 — Bỏ trần budget ứng dụng cho chatbot

## Giao cái gì

Bỏ sáu trần ứng dụng đã được yêu cầu rõ: số lần gọi model, token đầu vào, token đầu ra, số truy vấn graph, hạn lượt và độ dài câu hỏi. Giữ fact đã kiểm chứng, quyền riêng tư, ownership đã ghim và các giới hạn history/retrieval hiện có. Giới hạn và chi phí của provider sống là bên ngoài ứng dụng.

## Ngoài phạm vi

Không đổi contract câu trả lời grounded. Không suy release readiness từ task `done` khi Component Merge Gate còn pending.

## Task

- TASK-RKG-036
