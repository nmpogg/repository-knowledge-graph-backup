---
uid: null
key: TASK-RKG-019
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
  - TASK-RKG-002
  - TASK-RKG-014
  blocked_by: []
  implements:
  - FR-RKG-005
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-019.yaml
  plan: PLAN-TASK-RKG-019.md
  diary: DIARY-TASK-RKG-019.md
---
# TASK-RKG-019 — LLM provider interface and adapter

Implement structured provider interface, mock contract, timeout/token budgets and one
real adapter selected by OQ-RKG-001. Mock-only pass does not complete live acceptance.
Verify provider-side budgets and timeout behavior in AC-RKG-063.

## Result

- Structured provider protocol, deterministic mock, OpenRouter adapter using
  `openai/gpt-4o-mini`, bundled `o200k_base` tokenizer, JSON Schema validation,
  shared turn budgets and safe error codes are implemented.
- Unit contract, full regression suite, and live OpenRouter smoke test pass on
  the current tree. See `DIARY-TASK-RKG-019-r3` and
  `TEST-RKG-OPENROUTER-LIVE-001` for current-tree verification.
- HTTP mapping and grounded Q&A orchestration remain with T-020/021; this task
  verifies provider-side AC-RKG-063 limits and timeout behavior.
- `OPENROUTER_MODEL` selects the OpenRouter model; absent/blank keeps the
  OQ-RKG-001 default `openai/gpt-4o-mini`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-019.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-019.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-019.md) — kết quả, evidence và các correction.
