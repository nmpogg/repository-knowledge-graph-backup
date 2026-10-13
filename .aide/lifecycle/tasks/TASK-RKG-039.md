---
key: TASK-RKG-039
type: task
group: normative
scope: lifecycle
system: SYS-RKG
revision: 6
change_set: CHG-RKG-2026-006
story: STORY-RKG-033
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
authorization: CR-RKG-021
implementation_branch: fix/chatbot
component_merge_gate: pending
implementation_record:
  context: CTX-TASK-RKG-039-r2.yaml
  plan: PLAN-TASK-RKG-039-r3.md
  revision_plan: PLAN-TASK-RKG-039-r3.md
  diary: DIARY-TASK-RKG-039-r3.md
phase: implementation_author_verified_human_accepted_review_limit_exception_pending_gate
baseline: BL-CHG-RKG-2026-006-r1
review_package: RVP-TASK-RKG-039-r3
verification_evidence: TEST-TASK-RKG-039-004
review_record: REV-TASK-RKG-039-002
resolved_findings:
- FND-TASK-RKG-039-001
accepted_author_repairs:
- FND-TASK-RKG-039-002
review_limit_disposition: DEC-TASK-RKG-039-001
---
# TASK-RKG-039 — Enable verbose terminal chatbot debugging

Honor explicit terminal debug authorization with complete model/validator traces and configured-key masking. No raw debug content in storage/API/evidence. Preserve grounded behavior and budgets; done requires current-tree verification and independent review.
