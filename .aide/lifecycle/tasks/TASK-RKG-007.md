---
uid: null
key: TASK-RKG-007
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-005
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-003
  - TASK-RKG-006
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-007.yaml
  plan: PLAN-TASK-RKG-007.md
  diary: DIARY-TASK-RKG-007.md
---
# TASK-RKG-007 — Python metadata adapter and package inventory

Implement Python metadata readers for pyproject/requirements/uv/poetry with provenance
and map import to distribution without name guessing. Metadata conventions stay inside
the adapter; core receives generic dependency/detection records. Verify AC-RKG-021/022.

## Result

`PythonLanguageAdapter` reads static project, requirements and lock metadata from the
immutable source manifest. It emits versioned detection evidence and canonical
`ExternalDependency` facts with declaration/lock provenance, groups, markers,
`lock_only` and `declared_no_observed_import` states. Explicit import ownership
links supported imports and callable symbol usage without guessing from names or
executing analyzed source. Local modules shadow external names.

Verification: `TEST-RKG-PKG-INVENTORY` and `DIARY-TASK-RKG-007`, checked against
code revision `4e902ebd2e86dbfe8a7afd8e491ecaf25a73168e`.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-007.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-007.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-007.md) — kết quả, evidence và các correction.
