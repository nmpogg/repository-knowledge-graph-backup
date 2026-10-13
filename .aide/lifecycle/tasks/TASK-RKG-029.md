---
key: TASK-RKG-029
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-019
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-003-TEAM-RKG
  depends_on:
  - TASK-RKG-006
  - TASK-RKG-009
  - TASK-RKG-010
  - TASK-RKG-013
  - TASK-RKG-017
  - TASK-RKG-028
  implements:
  - FR-RKG-002
  - FR-RKG-003
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-029.yaml
  plan: PLAN-TASK-RKG-029.md
  diary: DIARY-TASK-RKG-029.md
---
# TASK-RKG-029 - Focused entity flow graph

User authorized branch creation and implementation on 2026-10-01. Branch:
feat/focused-flow-graph. Scope: focused root-specific traversal, optional ownership
and dependency overlays, matching context export and static receiver/data access
resolution needed to follow endpoint/service/repository/database flows.

Verification covers AC-RKG-009 (traversal), AC-RKG-010 (context) and
AC-RKG-013 (database resources), which this story satisfies, plus checks that
other stories own: AC-RKG-003 and AC-RKG-073 belong to STORY-RKG-017, AC-RKG-007
is listed by STORY-RKG-004 and STORY-RKG-017, and AC-RKG-020 belongs to
STORY-RKG-005. Revision 5 listed AC-RKG-073 on this story. No source execution;
no shared generic method-to-all-tables edges. Dynamic or ambiguous paths remain explicit diagnostics. Runtime re-indexing
may publish a new snapshot while preserving prior snapshots/conversation pins.

Record current-tree code/artifact revision and hashes in TEST-RKG-FOCUSED-FLOW-001
before setting done. All change-set gates remain pending; historical records are
append-only and unchanged.

Current-tree verification completed on 2026-10-01. Evidence:
[TEST-RKG-FOCUSED-FLOW-001](../../evidence/tests/TEST-RKG-FOCUSED-FLOW-001.md),
including base revision and code/artifact SHA-256 fingerprints. Backend: 184 passed,
6 skipped; frontend: 54 passed; build, lint and diff checks passed. Isolated soopi
index: 34 endpoints; cart/guest-cart/category flows reach their proved tables without
ownership fan-out. The running user backend and snapshots were preserved; restart
and re-index applies new extraction. No interactive browser review or gate approval
is claimed. Normative gate state remains pending.

Reopened after user feedback on 2026-10-01: prior verification did not establish
visual usability. Correct flow layout, ownership presentation, edge readability,
selection camera behavior and detection of a running backend that ignores flow.
Current correction evidence will be TEST-RKG-FOCUSED-FLOW-002; prior evidence remains
unchanged. Verify the actual soopi flow in a browser before closing this revision.

Correction verified on 2026-10-01 in
[TEST-RKG-FOCUSED-FLOW-002](../../evidence/tests/TEST-RKG-FOCUSED-FLOW-002.md),
including real browser screenshots and current-tree hashes. Frontend: 59 passed;
post-copy/mock-location focused checks: 12 passed; backend flow/API checks: 15 passed;
build/lint/Ruff/diff checks passed. Actual browser verification covers cart/category
flows, ownership captions, stable selection viewport and legacy-backend rejection.
The original running backend/database are preserved; current implementation is
available in the isolated loopback preview. Gates remain pending.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-029.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-029.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-029.md) — kết quả, evidence và các correction.
