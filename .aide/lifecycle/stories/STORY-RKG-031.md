---
key: STORY-RKG-031
group: normative
scope: lifecycle
system: SYS-RKG
revision: 2
authorization: CR-RKG-019
verification_evidence: TEST-TASK-RKG-037-003
review_record: REV-TASK-RKG-037-002
change_set: CHG-RKG-2026-004
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
implementation_task: TASK-RKG-037
phase: implementation_verified_independently_reviewed_pending_gate_decision
---
# STORY-RKG-031 — Chọn provider OpenAI trực tiếp

## Giao cái gì

Thêm lựa chọn OpenAI cạnh OpenRouter, do server chọn rõ ràng, cùng ranh giới hội thoại grounded. Giữ mặc định hiện có, kiểm tra schema/graph, quyền riêng tư và budget ứng dụng không trần. Không fallback tự động và không đổi contract giao diện.

## Ngoài phạm vi

Không gọi provider sống trong story này. Không đổi cấu hình operator. Không suy release readiness khi Component Merge Gate còn pending.

## Task

- TASK-RKG-037
