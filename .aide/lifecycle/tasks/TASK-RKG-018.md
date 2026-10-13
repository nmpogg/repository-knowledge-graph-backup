---
uid: null
key: TASK-RKG-018
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-012
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 9
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-004-TEAM-RKG
  depends_on:
  - TASK-RKG-013
  - TASK-RKG-014
  implements:
  - FR-RKG-005
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-018.yaml
  plan: PLAN-TASK-RKG-018.md
  diary: DIARY-TASK-RKG-018.md
---
# TASK-RKG-018 — Conversation persistence and state

Implement conversation/turn/state storage, snapshot pin/retention, revision,
idempotency, deterministic Turn identity, redaction and restart recovery. Verify
AC-RKG-030/031/033/044/045/059/064.

## Kết quả

- `src/rkg/conversations/`: pin snapshot, deterministic `Turn.id`, revision and
  idempotency, redaction, pending recovery on `Storage` open.
- Service codes map to the API contract: `invalid_turn_request` (422),
  `conversation_conflict` / `conversation_busy` (409), `snapshot_unavailable`
  (410). HTTP routes stay with T-016/T-021. History window (AC-RKG-032) stays
  with T-020 / STORY-RKG-013. Current plan is `PLAN-TASK-RKG-018-r2`.
  `PLAN-TASK-RKG-018` revision 1 remains the historical plan and listed
  AC-RKG-032 on this task.
- Positive `expected_revision` that is not current is `conversation_conflict`.
  Missing, non-integer or non-positive revision is `invalid_turn_request`.
- Evidence: `DIARY-TASK-RKG-018`, `TEST-RKG-CONVERSATION-STATE-001`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-018.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-018.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-018.md) — kết quả, evidence và các correction.
