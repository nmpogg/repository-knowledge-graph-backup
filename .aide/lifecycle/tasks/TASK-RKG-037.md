---
key: TASK-RKG-037
type: task
group: normative
scope: lifecycle
system: SYS-RKG
revision: 5
change_set: CHG-RKG-2026-004
story: STORY-RKG-031
status: done
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-074
- AC-RKG-080
authorization: CR-RKG-019
implementation_branch: fix/chatbot
component_merge_gate: pending
implementation_record:
  context: CTX-TASK-RKG-037-r2.yaml
  plan: PLAN-TASK-RKG-037-r2.md
  diary: DIARY-TASK-RKG-037-r2.md
phase: implementation_verified_independently_reviewed_pending_gate_decision
baseline: BL-CHG-RKG-2026-004-r2
review_package: RVP-TASK-RKG-037-r2
verification_evidence: TEST-TASK-RKG-037-003
review_record: REV-TASK-RKG-037-002
resolved_findings:
- FND-TASK-RKG-037-001
- FND-TASK-RKG-037-002
- FND-TASK-RKG-037-003
---
# TASK-RKG-037 — Add direct OpenAI provider

Implement explicit OpenAI/OpenRouter selection with the same grounded conversation boundary. Done requires current-tree verification and independent review. No historical approval is transferred.
