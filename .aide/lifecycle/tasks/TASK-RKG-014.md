---
uid: null
key: TASK-RKG-014
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-008
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
  - TASK-RKG-013
  implements:
  - FR-RKG-003
  - FR-RKG-004
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-014.yaml
  plan: PLAN-TASK-RKG-014.md
  diary: DIARY-TASK-RKG-014.md
---
# TASK-RKG-014 — Search, traversal and context services

Implement deterministic search/BFS/context with direction, filters, paging, budget,
cycle handling and safe truncation. Verify AC-RKG-009/010/036/037/060/062.

## Kết quả

- `src/rkg/graph/`: `search_entities`, `get_entity`, `traverse_subgraph`,
  `build_context` + typed guards (`no_active_snapshot`, `snapshot_unavailable`,
  `not_found`, `invalid_budget`). Truncation reasons:
  `depth_limit` / `max_nodes` / `max_edges` / `max_chars`.
- AC-RKG-009/010/036/060 verified at service layer.
  AC-RKG-037/062 (p95 benchmark reports) deferred to T-016/T-022 per operator.
- Evidence: `DIARY-TASK-RKG-014`, `TEST-RKG-GRAPH-READS-001`.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-014.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-014.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-014.md) — kết quả, evidence và các correction.
