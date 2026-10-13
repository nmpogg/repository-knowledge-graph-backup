---
uid: null
key: TASK-RKG-010
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-006
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-006
  - TASK-RKG-008
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-010.yaml
  plan: PLAN-TASK-RKG-010.md
  diary: DIARY-TASK-RKG-010.md
---
# TASK-RKG-010 — SQLAlchemy 2.x data-access adapter

Extract declarative model/table mapping and supported reads/writes operations with
namespace/schema identity and evidence. Verify AC-RKG-013/014.

## Result

`SQLAlchemyDataAccessAdapter` implements the versioned data-access profile for
SQLAlchemy 2.x. Declarative classes with a literal `__tablename__` and a literal
or omitted schema become `DataResource` rows and `maps_to` edges. The same table
name in another namespace stays a different resource. Supported `get`, `select`,
`insert`, `update`, `delete` and `add` calls become `reads` or `writes` only
when execution evidence is present. An unresolved model expression on `get`, `add`
or `delete`, and an executed statement whose model does not resolve, produce
diagnostics and no guessed edge. Dynamic tables, reflection and a local module
named `sqlalchemy` do the same. Several operations from one callable onto one
resource stay one edge, with the lexicographically smallest rule on the edge
and every operation rule kept on evidence. Analyzed repository source is
never executed.

Verification: `TEST-RKG-SQLALCHEMY-ADAPTER-001` and `DIARY-TASK-RKG-010`, checked
against base revision `66680533506fa6b3ab4812ac1ed4a59c8f89a44a` plus the file
hashes in that diary.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-010.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-010.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-010.md) — kết quả, evidence và các correction.
