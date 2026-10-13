---
key: PLAN-TASK-RKG-020
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-020
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: 1f4b7475dd3bd6c8b1dd58cb561cdeea6d89718b
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-020.yaml
verification_targets:
- path: tests/integration/test_grounded_qa.py
  tests:
  - test_answer_and_followup_use_pinned_edges_and_citations
  - test_ambiguity_then_ordered_selection
  - test_injection_and_foreign_edge_fail_closed
  - test_timeout_keeps_focus_and_history_window_drops_old_turns
  - test_history_window_respects_4000_token_ceiling
  - test_db_event_dependency_and_technology_claims_are_cited
  - test_disabled_unknown_and_long_question_do_not_corrupt_graph
  - test_truncated_retrieval_is_reported_with_valid_citation
- path: tests/integration/test_grounded_qa_live.py
  tests:
  - test_openrouter_live_grounded_edge_and_citation
  - test_openrouter_live_db_event_dependency_technology
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-020
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-020
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-020
      - key: TASK-RKG-020
        revision: 1
  record: '# PLAN-TASK-RKG-020


    Trả lời bám context đã pin, citation thuộc context, follow-up dùng focus.


    ## Thứ tự


    1. `grounded service` — plan schema, retrieval read-only, citation check. Kiểm: AC-RKG-024, AC-RKG-042.

    2. `fallback` — needs_clarification, insufficient_evidence, llm_*. Kiểm: AC-RKG-025.

    3. `focus` — follow-up và đổi chủ đề. Kiểm: AC-RKG-028, AC-RKG-029.


    ## Không làm


    - Không thêm route HTTP.

    - Không chạy query ngoài allowlist.

    - Không bịa khi provider lỗi.'
---

# PLAN-TASK-RKG-020

Trả lời bám context đã pin, citation thuộc context, follow-up dùng focus.

## Thứ tự

1. `grounded service` — plan schema, retrieval read-only, citation check. Kiểm: AC-RKG-024, AC-RKG-042.
2. `fallback` — needs_clarification, insufficient_evidence, llm_*. Kiểm: AC-RKG-025.
3. `focus` — follow-up và đổi chủ đề. Kiểm: AC-RKG-028, AC-RKG-029.

## Không làm

- Không thêm route HTTP.
- Không chạy query ngoài allowlist.
- Không bịa khi provider lỗi.

## Phạm vi code và kiểm chứng

- `src/rkg/conversations/README.md`
- `src/rkg/conversations/__init__.py`
- `src/rkg/conversations/grounded.py`
- `src/rkg/conversations/service.py`
- `tests/integration/graph_helpers.py`
- `tests/integration/test_grounded_qa.py`
- `tests/integration/test_grounded_qa_live.py`

- `python -m pytest tests/integration/test_grounded_qa.py tests/integration/test_grounded_qa_live.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-020](../context/CTX-TASK-RKG-020.yaml). Kết quả triển khai: [DIARY-TASK-RKG-020](../diaries/DIARY-TASK-RKG-020.md).
