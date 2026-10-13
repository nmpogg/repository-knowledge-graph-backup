---
uid: null
key: TASK-RKG-005
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-004
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
  - TASK-RKG-004
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-005.yaml
  plan: PLAN-TASK-RKG-005.md
  diary: DIARY-TASK-RKG-005.md
---
# TASK-RKG-005 — Python language adapter: AST and lexical scope

Implement the first `LanguageAdapter` for CPython 3.12. Extract Python
entities/containment and build lexical symbol index without source execution; emit
only generic parsed-unit/`FactBatch` contracts. This task still checks
AC-RKG-006 and AC-RKG-035, which `STORY-RKG-004` satisfies, plus AC-RKG-001
on `STORY-RKG-003` and the shared adapter conformance suite. Current
`AC-RKG-002` ownership is `STORY-RKG-017`. Revision 5 listed AC-RKG-002 here.

## Result

The Python structural adapter and golden/negative fixtures are implemented at
`49e8909`. Current-tree verification, AC-to-test mapping and scope limits are
recorded in `.aide/evidence/diaries/DIARY-TASK-RKG-005.md`.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-005.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-005.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-005.md) — kết quả, evidence và các correction.
