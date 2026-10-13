---
key: TASK-RKG-033
group: normative
scope: lifecycle
system: SYS-RKG
revision: 4
change_set: CHG-RKG-2026-002
classification: internal
ai_assisted: true
type: task
story: STORY-RKG-022
status: done
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
  depends_on:
  - TASK-RKG-030
  - TASK-RKG-032
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-074
- AC-RKG-080
- AC-RKG-081
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-033-r2.yaml
  plan: PLAN-TASK-RKG-033.md
  diary: DIARY-TASK-RKG-033.md
phase: implementation_verified_independently_reviewed_component_approved
implementation_branch: fix/chatbot
authorization: CR-RKG-014
component_merge_gate: approved
review_record: REV-TASK-RKG-033-001
review_package: RVP-TASK-RKG-033-r1
verification_evidence: TEST-TASK-RKG-033-001
component_approval: approval-013
current_tree_readiness: TEST-RKG-CHATBOT-CLOSURE-001
---
# TASK-RKG-033 — Capabilities, locale/history và exact citation API

## Làm gì

- Expose coherent capability negotiation and optional ui_locale; old defaults/request identities retained.
- Return stored metadata on POST/history; optional include_unavailable preserves old default 410.
- Exact per-turn citation lookup verifies ownership/index/pinned evidence, no substitution or source excerpts.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.

## Current implementation completion

Current candidate hashes and approved normative pins match the independent pass record. Implementation subchecks are complete under the current-branch delivery instruction CR-RKG-014. Human Component Merge signature, downstream full AC acceptance, live-provider quality and release are not implied.
