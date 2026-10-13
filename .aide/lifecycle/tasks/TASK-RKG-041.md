---
key: TASK-RKG-041
type: task
group: normative
scope: lifecycle
system: SYS-RKG
revision: 5
change_set: CHG-RKG-2026-008
story: STORY-RKG-035
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
- AC-RKG-075
- AC-RKG-080
authorization: CR-RKG-023
implementation_branch: fix/chatbot
component_merge_gate: pending
implementation_record:
  context: CTX-TASK-RKG-041-r2.yaml
  plan: PLAN-TASK-RKG-041.md
  revision_plan: PLAN-TASK-RKG-041-r2.md
  diary: DIARY-TASK-RKG-041-r2.md
phase: implementation_verified_independently_reviewed_pending_gate_decision
baseline: BL-CHG-RKG-2026-008-r1
review_package: RVP-TASK-RKG-041-r2
verification_evidence: TEST-TASK-RKG-041-003
review_record: REV-TASK-RKG-041-002
---
# TASK-RKG-041 — Handle natural entity and source-location questions

Verify complete user question flow without a preselected root, preserving pinned facts, strict validation and honest ambiguity.
