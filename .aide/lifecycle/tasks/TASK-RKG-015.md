---
uid: null
key: TASK-RKG-015
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-009
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
  - TASK-RKG-004
  - TASK-RKG-009
  - TASK-RKG-010
  - TASK-RKG-011
  - TASK-RKG-012
  - TASK-RKG-013
  implements:
  - FR-RKG-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-015.yaml
  plan: PLAN-TASK-RKG-015.md
  diary: DIARY-TASK-RKG-015.md
---
# TASK-RKG-015 — Index job coordinator and CLI

Compose repository-scoped ingestion/detection/extraction/publication, serialize jobs,
recover interrupted work and implement repository/snapshot/index/serve CLI commands.
Verify AC-RKG-008/012/034/038/039/049/050/055/067…071.

Implementation verification: `TEST-RKG-INDEX-JOB-CLI-001`. The benchmark for
AC-RKG-039 is scheduled with the pilot corpus in `TASK-RKG-022`; API/UI portions
of the shared ACs remain with their transport and web tasks.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-015.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-015.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-015.md) — kết quả, evidence và các correction.
