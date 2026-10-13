---
uid: null
key: TASK-RKG-020
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-013
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 10
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-004-TEAM-RKG
  depends_on:
  - TASK-RKG-018
  - TASK-RKG-019
  implements:
  - FR-RKG-005
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-020.yaml
  plan: PLAN-TASK-RKG-020.md
  diary: DIARY-TASK-RKG-020.md
---
# TASK-RKG-020 — History-aware grounded Q&A

Implement follow-up resolution, bounded history, clarification, read-only retrieval,
synthesis and citation validation. Verify AC-RKG-024/025/028/029/032/042/063/064.

## Result

- `submit_grounded_turn` links persisted conversation state, a bounded history
  window, schema-limited planning, pinned read-only graph retrieval and a
  synthesis step that selects only supported edge IDs. Relation text and
  citations are rendered from validated graph facts/evidence.
- Explicit root, named entity, ordered clarification selection and pronoun
  follow-up retain or replace focus deterministically. Unknown, ambiguous or
  truncated input and disabled, malformed or timed-out providers return safe
  statuses/codes.
- Service and live-provider checks cover the task's ACs; full current-tree
  verification and limitations are recorded in `DIARY-TASK-RKG-020-r2` and
  `TEST-RKG-GROUNDED-QA-002`. HTTP routes remain T-021; pilot-scale eval is
  T-022.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-020.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-020.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-020.md) — kết quả, evidence và các correction.
