---
uid: null
key: TASK-RKG-003
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-003
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
  - TASK-RKG-002
  implements:
  - FR-RKG-001
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-003.yaml
  plan: PLAN-TASK-RKG-003.md
  diary: DIARY-TASK-RKG-003.md
---
# TASK-RKG-003 — Local source loader

Implement local source config, allow/ignore lists, immutable manifest/hash, size
limits và root/symlink guards. Không import/run source. Verify
AC-RKG-001/012/026/035/038/049/050/051/054.

## Kết quả

Local source policy, allow/ignore pattern handling, canonical path and link guards,
immutable in-memory manifest/hash, file count/size limits and path-free errors are
implemented in `src/rkg/ingestion/`. Component-level verification and file hashes
are recorded in `DIARY-TASK-RKG-003`. Job states, parse diagnostics, full report,
registration API/UI and end-to-end AC verification remain with dependent tasks.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-003.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-003.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-003.md) — kết quả, evidence và các correction.
