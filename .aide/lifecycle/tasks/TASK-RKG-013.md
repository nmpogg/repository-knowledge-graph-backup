---
uid: null
key: TASK-RKG-013
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-007
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 6
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-002
  implements:
  - FR-RKG-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-013.yaml
  plan: PLAN-TASK-RKG-013.md
  diary: DIARY-TASK-RKG-013.md
---
# TASK-RKG-013 — Kùzu storage and atomic snapshots

Implement versioned schema/migrations, repository persistence/optimistic revision,
graph validation, atomic snapshot publication/activation/deletion and ownership/
reader/reference guards per `TBL-RKG-GRAPH`. Verify AC-RKG-007/008/066…071.

## Kết quả

- `src/rkg/storage/` + `src/rkg/graph/` với SchemaMeta migrations, publish
  auto-activate, delete guards, in-process reader pins.
- DDL/TBL revision 9: SchemaMeta + multi-FROM DEPENDS_ON; physical entity PK
  snapshot-qualified.
- Evidence: `DIARY-TASK-RKG-013`, `TEST-RKG-STORAGE-SNAPSHOTS-001`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-013.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-013.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-013.md) — kết quả, evidence và các correction.
