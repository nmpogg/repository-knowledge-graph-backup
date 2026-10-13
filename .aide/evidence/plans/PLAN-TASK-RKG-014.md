---
key: PLAN-TASK-RKG-014
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-014
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 4399660b46a8362ec9d87652795d023318ea6dbc
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-014.yaml
verification_targets:
- path: tests/integration/test_graph_reads.py
  tests:
  - test_ac036_search_match_order_paging_and_snapshot_isolation
  - test_ac009_traversal_cycle_direction_filter_deterministic
  - test_ac010_context_deterministic_budget_and_no_secrets
  - test_ac060_guards_no_active_unavailable_identity
  - test_ac036_endpoint_method_path_query
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-014
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-014
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-014
      - key: TASK-RKG-014
        revision: 1
  record: '# PLAN-TASK-RKG-014


    Đọc snapshot đã pin: search, BFS có visited set, context deterministic trong budget.


    ## Thứ tự


    1. `search` — type, qualified name, paging deterministic, đúng snapshot. Kiểm: AC-RKG-036.

    2. `traversal` — direction, edge types, depth, cycle. Kiểm: AC-RKG-009.

    3. `context` — lặp lại payload, truncation_reasons. Kiểm: AC-RKG-010.

    4. `missing snapshot` — 409 hoặc 410 hoặc 404, không graph rỗng giả. Kiểm: AC-RKG-060.


    ## Không làm


    - Không đo p95 ở đây (TASK-RKG-022).

    - Không trả raw source hay secret trong context.'
---

# PLAN-TASK-RKG-014

Đọc snapshot đã pin: search, BFS có visited set, context deterministic trong budget.

## Thứ tự

1. `search` — type, qualified name, paging deterministic, đúng snapshot. Kiểm: AC-RKG-036.
2. `traversal` — direction, edge types, depth, cycle. Kiểm: AC-RKG-009.
3. `context` — lặp lại payload, truncation_reasons. Kiểm: AC-RKG-010.
4. `missing snapshot` — 409 hoặc 410 hoặc 404, không graph rỗng giả. Kiểm: AC-RKG-060.

## Không làm

- Không đo p95 ở đây (TASK-RKG-022).
- Không trả raw source hay secret trong context.

## Phạm vi code và kiểm chứng

- `src/rkg/domain/README.md`
- `src/rkg/graph/README.md`
- `src/rkg/graph/__init__.py`
- `src/rkg/graph/access.py`
- `src/rkg/graph/context.py`
- `src/rkg/graph/context_build.py`
- `src/rkg/graph/errors.py`
- `src/rkg/graph/search.py`
- `src/rkg/graph/traversal.py`
- `tests/integration/graph_helpers.py`
- `tests/integration/test_graph_reads.py`

- `python -m pytest tests/integration/test_graph_reads.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-014](../context/CTX-TASK-RKG-014.yaml). Kết quả triển khai: [DIARY-TASK-RKG-014](../diaries/DIARY-TASK-RKG-014.md).
