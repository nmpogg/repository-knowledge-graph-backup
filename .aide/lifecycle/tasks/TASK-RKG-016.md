---
uid: null
key: TASK-RKG-016
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-010
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
  - TASK-RKG-014
  - TASK-RKG-015
  implements:
  - FR-RKG-001
  - FR-RKG-003
  - FR-RKG-004
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-016.yaml
  plan: PLAN-TASK-RKG-016.md
  diary: DIARY-TASK-RKG-016.md
---
# TASK-RKG-016 — Core FastAPI transport

Implement repository CRUD, repository-scoped job, snapshot lifecycle, entity/
technology/dependency/diagnostic/subgraph/context endpoints, CLI parity and local
access guards per `API-RKG-CORE-v1`. Verify AC-RKG-009/010/012/026/034/036/040/041/
044/045/055/058/060/061/062/066…072.

## Kết quả

- `src/rkg/api/`: FastAPI `/api/v1` over the existing storage, graph and index
  services. `rkg serve` runs that app on `127.0.0.1` with one worker.
- Mutations require `X-RKG-Session` and a loopback Host. A present Origin must
  also be loopback. The token is `RKG_SESSION_TOKEN` or an in-memory token that
  the CLI does not print.
- AC-RKG-009/010/012/026/034/036/040/041/044/045/055/058/060/061/066–072 verified
  at the HTTP boundary by `TEST-RKG-CORE-API-001`.
- AC-RKG-062 (context p95) stays with `TASK-RKG-022`; there is no pilot corpus yet.
- Conversation create, list and turn routes stay with `TASK-RKG-021`. Delete is
  implemented so a pending turn returns `409 conversation_busy`.
- Evidence: `DIARY-TASK-RKG-016`, `TEST-RKG-CORE-API-001`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-016.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-016.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-016.md) — kết quả, evidence và các correction.
