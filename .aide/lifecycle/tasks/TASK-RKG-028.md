---
key: TASK-RKG-028
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-018
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 5
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-008
  - TASK-RKG-009
  - TASK-RKG-027
  implements:
  - FR-RKG-002
  - FR-RKG-003
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-028.yaml
  plan: PLAN-TASK-RKG-028.md
  diary: DIARY-TASK-RKG-028.md
---
# TASK-RKG-028 - FastAPI static indexing coverage

User authorized all four diagnosed corrections on 2026-10-01: unverified-version
selection, local app factories, literal router loops and empty route paths.

## Scope and acceptance

- Opt-in best-effort FastAPI extraction when version is unknown; retain
  version_unverified and a diagnostic. Known incompatible versions stay blocked;
  generic adapters keep strict constraints unless they explicitly opt in.
- Resolve a unique local parameterless factory with one direct app construction
  and one unconditional return. Preserve source locations and handler identities.
- Expand finite literal list/tuple router loops without evaluating Python.
  Ambiguous/dynamic registration emits diagnostics, not guessed routes.
- Empty route paths inherit the effective prefix without an added trailing slash.
- Verify synthetic regressions, full backend and a manifest-backed soopi scan.
  Record checked code revision/hashes under .aide/evidence/ before marking done.

AC-RKG-004 (routes), AC-RKG-005 (dependency wiring), AC-RKG-007 (evidence),
AC-RKG-020 (support states), AC-RKG-040 (application choice) and AC-RKG-052
(single-app selection) are verified against current requirement text.
Historical evidence remains unchanged and change-set gates remain pending.

## Completion evidence

[TEST-RKG-FASTAPI-STATIC-002](../../evidence/tests/TEST-RKG-FASTAPI-STATIC-002.md)
identifies checked code/artifact revisions and digests. Full backend: 178 passed,
6 skipped. Ruff and whitespace checks passed. Isolated soopi indexing and re-indexing
the existing registration both published 34 endpoints with 34 handler links. New
active snapshot was verified and the previous snapshot retained. Backend was stopped
and was not restarted; browser interaction was not automated. Version uncertainty
and unsupported dynamic patterns remain explicit in diagnostics.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-028.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-028.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-028.md) — kết quả, evidence và các correction.
