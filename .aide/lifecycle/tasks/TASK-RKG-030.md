---
key: TASK-RKG-030
group: normative
scope: lifecycle
system: SYS-RKG
revision: 8
change_set: CHG-RKG-2026-002
classification: internal
ai_assisted: true
type: task
story: STORY-RKG-020
status: done
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-006-TEAM-RKG
  depends_on: []
  implements:
  - FR-RKG-005
satisfies:
- AC-RKG-077
- AC-RKG-080
baseline: BL-CHG-RKG-2026-002-r8
implementation_record:
  context: CTX-TASK-RKG-030-r3.yaml
  plan: PLAN-TASK-RKG-030-r4.md
  diary: DIARY-TASK-RKG-030-r3.md
  plan_supplement: PLAN-TASK-RKG-030-r2
phase: accepted_component_storage_complete
verification_evidence: TEST-RKG-CHATBOT-STORAGE-004
implementation_branch: feat/chatbot-storage-revision
component_merge_gate: approved
execution_state: completed
pause_evidence: CR-RKG-011
checkpoint_branch: fix/chatbot
resume_evidence: CR-RKG-012
review_findings: []
review_record: REV-RKG-2026-010
finding_remediation: FIX-TASK-RKG-030-003
review_package: RVP-TASK-RKG-030-r3
resolved_findings:
  FND-TASK-RKG-030-002: REV-RKG-2026-010
  FND-TASK-RKG-030-003: REV-RKG-2026-010
review_round_limit_reached: true
review_workflow:
  rounds_completed: 2
  automatic_third_pass: false
  authority_decision: approved_with_one_time_review_exception
component_approval: approval-012
accepted_findings:
  FND-TASK-RKG-030-001: approval-012
---
# TASK-RKG-030 — Migration v3 và lưu metadata/pending intent

## Làm gì

- Add guarded atomic 2→3 dispatcher; preserve old pins/rows/hash/state, verified no-op and rollback.
- Persist typed bounded response metadata in the terminal transaction; legacy/future metadata maps to unknown.
- Add explicit preserve/replace/clear pending-intent updates without losing original question or state on errors/restart.

## Xong khi

Kiểm chứng subchecks thuộc task bằng current-tree tests, lưu hash code/contract và AC coverage trong evidence trước khi đổi done. Các AC ở task nền chỉ là đóng góp; task downstream mới xác nhận hành vi end-to-end. Không sửa signed normative sources.

## Current handoff

Implementation candidate verified in the isolated feat/chatbot-storage-v3 worktree: 222 backend tests pass, Ruff/diff pass. Main checkout product files restored. Independent adversarial code review and Component Merge Gate remain pending; status stays in_progress. No operator DB migration or full AC acceptance claimed.

## Paused checkpoint

CR-RKG-011 requests a temporary stop and local checkpoint on the user-created fix/chatbot branch. The exact frozen TASK030 code/test bytes are copied from its isolated worktree for this checkpoint. Task remains in_progress; no independent review/merge gate approval, deployment or DB migration is implied.

## Revision after REV009

CR-RKG-012 resumes only the three blocker repairs on feat/chatbot-storage-revision. 70 focused checks and 258 synthetic backend checks pass for the new frozen candidate. All three finding IDs remain pending independent verification; task stays in_progress and Component Merge pending. Primary checkpoint code is unchanged.

## Remaining001 repair after round2

Native relationship multiplicity is checked without row export/write probes.348 synthetic tests pass for frozen package r3;002/003 retain independent resolved status.001 remains open in REV010 until gate-authority disposition. B.18 two-round ceiling reached; no automatic third review or merge initiated.

## Human acceptance after review ceiling

PhongNM accepts frozen r3 under CR-RKG-013 and approval-012. Exact recovery matches all 10 candidate hashes and all 36 normative pins; current-tree validation passes 348 synthetic tests, Ruff lint and whitespace checks. FND001 is accepted by gate authority with a one-time review exception, not independently resolved; FND002/003 retain REV010 resolved status. TASK030 storage contribution is done; downstream AC acceptance, UI/live-provider checks and operator migration remain pending. Accepted code is retained on feat/chatbot-storage-revision.
