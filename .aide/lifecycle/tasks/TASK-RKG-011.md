---
uid: null
key: TASK-RKG-011
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-006
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
  - TASK-RKG-006
  - TASK-RKG-008
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-011.yaml
  plan: PLAN-TASK-RKG-011.md
  diary: DIARY-TASK-RKG-011.md
---
# TASK-RKG-011 — aiokafka messaging adapter

Extract topic-level publishes/consumes for the supported producer/consumer patterns;
dynamic topic stays unresolved. Verify AC-RKG-015.

## Result

`AIOKafkaMessagingAdapter` implements the versioned messaging profile for
aiokafka. Literal topics and unique module constants on `send`, `send_and_wait`,
`send_batch`, `AIOKafkaConsumer(*topics)` and `subscribe` become `publishes` or
`consumes` edges to one `MessageChannel` per topic name. The namespace is empty.
A receiver that does not uniquely resolve, including a `self` or `cls` client
attribute assigned more than once, produces a diagnostic and no edge. Dynamic
topics, pattern subscriptions and calls outside a callable do the same.
Payloads are not stored. Analyzed repository source is never executed.

Verification: `TEST-RKG-AIOKAFKA-ADAPTER-001` and `DIARY-TASK-RKG-011`, checked
against base revision `66680533506fa6b3ab4812ac1ed4a59c8f89a44a` plus the file
hashes in that diary.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-011.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-011.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-011.md) — kết quả, evidence và các correction.
