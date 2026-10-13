---
key: TASK-RKG-032
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
  - TASK-RKG-031
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-076
- AC-RKG-079
- AC-RKG-081
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-032-r3.yaml
  plan: PLAN-TASK-RKG-032.md
  diary: DIARY-TASK-RKG-032.md
implementation_branch: fix/chatbot
authorization: CR-RKG-014
component_merge_gate: approved
phase: implementation_verified_independently_reviewed_component_approved
review_record: REV-TASK-RKG-032-003
review_package: RVP-TASK-RKG-032-r4
verification_evidence: TEST-TASK-RKG-032-004
component_approval: approval-013
current_tree_readiness: TEST-RKG-CHATBOT-CLOSURE-001
---
# TASK-RKG-032 — Validate narrative references và render câu trả lời

## Làm gì

- Wire read-plan v2/narrative v1 provider schemas; budgets/input preflight remain fixed.
- Validate root/anchor/direction/path/evidence/cycles in full; fail closed, no salvage/repair.
- Render direct/indirect vi/en relations, Endpoint handler bridge and exact claim/citation bindings.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.

## Current implementation completion

Current candidate hashes and approved normative pins match the independent pass record. Implementation subchecks are complete under the current-branch delivery instruction CR-RKG-014. Human Component Merge signature, downstream full AC acceptance, live-provider quality and release are not implied.
