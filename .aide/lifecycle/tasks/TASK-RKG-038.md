---
key: TASK-RKG-038
type: task
group: normative
scope: lifecycle
system: SYS-RKG
revision: 5
change_set: CHG-RKG-2026-005
story: STORY-RKG-032
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
authorization: CR-RKG-020
implementation_branch: fix/chatbot
component_merge_gate: pending
implementation_record:
  context: CTX-TASK-RKG-038-r2.yaml
  plan: PLAN-TASK-RKG-038-r2.md
  diary: DIARY-TASK-RKG-038-r2.md
phase: implementation_verified_independently_reviewed_pending_gate_decision
baseline: BL-CHG-RKG-2026-005-r1
review_package: RVP-TASK-RKG-038-r2
verification_evidence: TEST-TASK-RKG-038-003
review_record: REV-TASK-RKG-038-002
resolved_findings:
- FND-TASK-RKG-038-001
---
# TASK-RKG-038 — Diagnose malformed turns and clarify failed responses

Implement existing grounded input and privacy contracts, retaining strict output rejection and safe committed state. Exact live incident cause is not inferred from generic error text. Done requires current-tree verification and independent review.
