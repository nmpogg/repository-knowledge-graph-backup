---
key: TASK-RKG-036
type: task
group: normative
scope: lifecycle
system: SYS-RKG
revision: 5
change_set: CHG-RKG-2026-003
story: STORY-RKG-030
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
- AC-RKG-077
- AC-RKG-078
- AC-RKG-080
implementation_record:
  context: CTX-TASK-RKG-036-r1.yaml
  plan: PLAN-TASK-RKG-036-r2.md
  diary: DIARY-TASK-RKG-036-r2.md
authorization: CR-RKG-018
component_merge_gate: pending
implementation_branch: fix/chatbot
phase: implementation_verified_independently_reviewed_pending_gate_decision
baseline: BL-CHG-RKG-2026-003-r1
review_package: RVP-TASK-RKG-036-r2
verification_evidence: TEST-TASK-RKG-036-003
review_record: REV-TASK-RKG-036-002
resolved_findings:
- FND-TASK-RKG-036-001
---
# TASK-RKG-036 — Bỏ trần budget ứng dụng cho chatbot

Remove the six explicitly requested application ceilings, keeping validated facts, privacy, pinned ownership and existing history/retrieval limits. Done requires current-tree evidence and independent review; live-provider limits and charges are external.
