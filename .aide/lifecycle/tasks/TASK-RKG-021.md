---
uid: null
key: TASK-RKG-021
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-014
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  part_of:
  - EPIC-004-TEAM-RKG
  depends_on:
  - TASK-RKG-016
  - TASK-RKG-024
  - TASK-RKG-020
  implements:
  - FR-RKG-005
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-021.yaml
  plan: PLAN-TASK-RKG-021.md
  diary: DIARY-TASK-RKG-021.md
---
# TASK-RKG-021 — Conversation API and UI

Implement create/open/delete/history/follow-up/clarification/conflict UX and connect
it to conversation services. Verify
AC-RKG-028…033/041/042/044…047/059/063/064 end-to-end.

## Result

- `src/rkg/api` now creates, lists, reads and submits conversations through
  `rkg.conversations`. Delete still returns `409 conversation_busy` while a
  turn is pending. Missing session/origin is `401` before the provider runs.
  A too-long or incomplete turn is `422`. Provider failure is `502`,
  `503 llm_disabled` or `504 llm_timeout` and does not move committed focus.
  A missing pin is `410 snapshot_unavailable` and is not retargeted.
- The Ask screens cover create, open, history, follow-up, ordered
  clarification, conflict with the draft kept, delete confirmation, citation
  evidence and provider-disabled recovery. Repository and model text is rendered
  as text.
- Verified on the current tree by `TEST-RKG-CONVERSATION-API-001` and
  `DIARY-TASK-RKG-021`. Pilot-scale rubric remains T-022.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-021.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-021.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-021.md) — kết quả, evidence và các correction.
