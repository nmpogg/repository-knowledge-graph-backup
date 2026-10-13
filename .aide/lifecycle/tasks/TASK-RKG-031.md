---
key: TASK-RKG-031
group: normative
scope: lifecycle
system: SYS-RKG
revision: 4
change_set: CHG-RKG-2026-002
classification: internal
ai_assisted: true
type: task
story: STORY-RKG-021
status: done
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
  depends_on:
  - TASK-RKG-030
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-074
- AC-RKG-075
- AC-RKG-077
- AC-RKG-078
- AC-RKG-079
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-031-r2.yaml
  plan: PLAN-TASK-RKG-031.md
  diary: DIARY-TASK-RKG-031.md
implementation_branch: fix/chatbot
authorization: CR-RKG-014
component_merge_gate: approved
phase: implementation_verified_independently_reviewed_component_approved
review_record: REV-TASK-RKG-031-002
review_package: RVP-TASK-RKG-031-r2
verification_evidence: TEST-TASK-RKG-031-002
component_approval: approval-013
current_tree_readiness: TEST-RKG-CHATBOT-CLOSURE-001
---
# TASK-RKG-031 — Language resolver, endpoint lookup và clarification

## Làm gì

- Resolve vi/en with identifier exclusion; default locale preserves legacy fingerprint.
- Exact method/path/type before paging; collisions/overflow clarify.
- Greeting guards with zero graph/model calls; ordinal/button resumes committed original intent, legacy asks restatement.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.

## Current implementation completion

Current candidate hashes and approved normative pins match the independent pass record. Implementation subchecks are complete under the current-branch delivery instruction CR-RKG-014. Human Component Merge signature, downstream full AC acceptance, live-provider quality and release are not implied.
