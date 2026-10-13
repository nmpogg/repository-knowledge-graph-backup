---
key: TASK-RKG-034
group: normative
scope: lifecycle
system: SYS-RKG
revision: 6
change_set: CHG-RKG-2026-002
classification: internal
ai_assisted: true
type: task
story: STORY-RKG-023
status: done
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
  depends_on:
  - TASK-RKG-033
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-074
- AC-RKG-077
- AC-RKG-078
- AC-RKG-079
- AC-RKG-080
- AC-RKG-081
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-034-r4.yaml
  plan: PLAN-TASK-RKG-034-r3.md
  diary: DIARY-TASK-RKG-034-r2.md
implementation_branch: fix/chatbot
authorization: CR-RKG-014
component_merge_gate: approved
phase: implementation_verified_independently_reviewed_component_approved
review_record: REV-TASK-RKG-034-003
review_package: RVP-TASK-RKG-034-r3
verification_evidence: TEST-TASK-RKG-034-003
current_tree_readiness: TEST-RKG-CHATBOT-CLOSURE-001
resolved_findings:
- FND-TASK-RKG-034-001
- FND-TASK-RKG-034-002
- FND-TASK-RKG-034-003
- FND-TASK-RKG-034-004
component_approval: approval-013
---
# TASK-RKG-034 — Cập nhật Ask hiện có

## Làm gì

- Negotiate backend features; bind metadata/legacy unknown and unavailable history correctly.
- One primary answer with collapsed claims, clear ordered candidates, translated limitations and distinct errors.
- Exact source disclosure with safe identity/path/lines and keyboard/focus behavior, reuse existing Ask.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.
