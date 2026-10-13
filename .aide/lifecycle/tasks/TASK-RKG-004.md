---
uid: null
key: TASK-RKG-004
type: task
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
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
  - TASK-RKG-002
  - TASK-RKG-003
  implements:
  - NFR-RKG-EXT-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-004.yaml
  plan: PLAN-TASK-RKG-004.md
  diary: DIARY-TASK-RKG-004.md
---
# TASK-RKG-004 — Analyzer adapter contract and conformance suite

Implement versioned `LanguageAdapter`/`FrameworkAdapter` descriptors, registry,
generic parsed-unit/`FactBatch` boundary and shared conformance suite. Add the
test-only conformance fixture adapter and verify `NFR-RKG-EXT-001` through
`TEST-RKG-ADAPTER-CONFORMANCE` without modifying core coordinator, graph schema or API.
This task has no product AC. The generic "mỗi AC" sentence in
`CTX-TASK-RKG-004` does not assign an AC to it.

## Result

The versioned `rkg.adapter/v1` descriptors, registry, parsed-unit boundary and
shared conformance runner are implemented in `src/rkg/adapters/`. The comparison
revision `b10116e` contains the contract without the fixture. Revision `fd72965`
adds only the test adapter, fixture source and test registration. Current-tree
verification and the changed-file allowlist are recorded in
`.aide/evidence/tests/TEST-RKG-ADAPTER-CONFORMANCE.json`.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-004.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-004.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-004.md) — kết quả, evidence và các correction.
