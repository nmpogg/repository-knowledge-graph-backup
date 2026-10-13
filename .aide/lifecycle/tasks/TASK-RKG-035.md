---
key: TASK-RKG-035
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
  - TASK-RKG-034
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-074
- AC-RKG-075
- AC-RKG-076
- AC-RKG-077
- AC-RKG-078
- AC-RKG-079
- AC-RKG-080
- AC-RKG-081
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-035-r4.yaml
  plan: PLAN-TASK-RKG-035.md
  diary: DIARY-TASK-RKG-035-r2.md
phase: implementation_verified_independently_reviewed_component_approved
implementation_branch: fix/chatbot
review_package: RVP-TASK-RKG-035-r1
verification_evidence: TEST-TASK-RKG-035-001
review_record: REV-TASK-RKG-035-001
component_merge_gate: approved
current_tree_readiness: TEST-RKG-CHATBOT-CLOSURE-001
upstream_review_record: REV-TASK-RKG-034-003
component_approval: approval-013
---
# TASK-RKG-035 — Kiểm chứng AC và hồi quy toàn luồng

## Làm gì

- Verify malicious/foreign/cyclic/direction/schema outputs, budgets, replay, restart, concurrency and exact sources with synthetic fixtures.
- Run appropriate backend/frontend/build checks and browser interactions on the implemented Ask.
- Record pass/fail/not_run per AC; live provider acceptance needs actual authorized checks and is not fabricated.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.
