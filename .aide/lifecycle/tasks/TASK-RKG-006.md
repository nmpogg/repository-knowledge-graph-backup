---
uid: null
key: TASK-RKG-006
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-004
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 9
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-005
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-006.yaml
  plan: PLAN-TASK-RKG-006.md
  diary: DIARY-TASK-RKG-006.md
---
# TASK-RKG-006 — Python adapter import, call and class resolution

Within the Python language adapter, resolve imports, aliases, shadowing, static call
sites and explicit class relations; keep ambiguous/dynamic cases unresolved and emit
generic facts. This task's checks include AC-RKG-006/017/048, which
`STORY-RKG-004` still satisfies, and AC-RKG-021, which `STORY-RKG-005` satisfies.
Current `AC-RKG-003` ownership is `STORY-RKG-017`. Revision 6 listed AC-RKG-003
on this task under `STORY-RKG-004`.

## Result

Static Python resolution and negative fixtures are implemented at `c91e4d2`.
Current-tree verification, AC-to-test mapping and remaining cross-task AC scope
are recorded in `.aide/evidence/diaries/DIARY-TASK-RKG-006.md`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-006.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-006.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-006.md) — kết quả, evidence và các correction.
