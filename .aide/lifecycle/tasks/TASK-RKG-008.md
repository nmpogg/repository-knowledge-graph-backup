---
uid: null
key: TASK-RKG-008
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-005
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
  - TASK-RKG-005
  - TASK-RKG-007
  implements:
  - FR-RKG-002
  - NFR-RKG-EXT-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-008.yaml
  plan: PLAN-TASK-RKG-008.md
  diary: DIARY-TASK-RKG-008.md
---
# TASK-RKG-008 — Technology detection and adapter selection

Implement registry-driven detection/selection, FastAPI app candidates as the first
framework adapter, evidence/support report and explicit override validation. Core
selection must not branch on adapter ID. Verify AC-RKG-020/021/040/052/053/065 and
`TEST-RKG-ADAPTER-CONFORMANCE` from NFR-RKG-EXT-001.

## Result

`src/rkg/detection/` aggregates static metadata and import evidence, reports
`supported_patterns`, `detected_only`, `version_unverified` and
`unsupported_version`, and selects all compatible adapters from the registry.
The FastAPI detector finds ordered module-level application candidates via static
AST bindings. Exact application and adapter overrides are validated; a prior
application choice can be retained on re-index. Required entrypoints return
`app_selection_required` or `app_unresolved` without guessing.

Verification: `TEST-RKG-DETECT-001` and `DIARY-TASK-RKG-008`, checked against
code revision `51cede902a688529ebcd6ec164af7b3a86d826a0`. T-009 owns FastAPI
route/DI extraction; T-015 maps selection results to job/publish state.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-008.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-008.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-008.md) — kết quả, evidence và các correction.
