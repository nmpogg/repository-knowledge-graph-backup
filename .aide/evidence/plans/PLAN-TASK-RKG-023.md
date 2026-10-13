---
key: PLAN-TASK-RKG-023
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-023
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: 16208d8a1b93035ac7c705d0b130f0b890d0dbb7
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-023.yaml
verification_targets:
- path: tests/integration/test_grounded_qa_live.py
  tests:
  - test_openrouter_live_grounded_edge_and_citation
  - test_openrouter_live_db_event_dependency_technology
- path: tests/integration/test_openrouter_live.py
  tests:
  - test_openrouter_live_structured_response
- path: tests/integration/test_pilot_corpus.py
  tests:
  - test_pilot_has_reviewable_edges_in_every_required_stratum
  - test_grounded_retrieval_preserves_requested_pilot_relations
- path: tests/unit/test_local_source.py
  tests:
  - test_safe_source_with_shell_metacharacters_is_data_only
  - test_manifest_is_stable_and_keeps_original_bytes_after_source_changes
  - test_loader_keeps_valid_and_invalid_syntax_for_adapter_diagnostics
  - test_missing_outside_and_source_root_errors_hide_host_path
  - test_source_root_and_ignore_allow_lists
  - test_file_limit_is_fail_closed_and_large_file_is_skipped
  - test_oversized_file_is_not_read
  - test_symlink_escape_is_rejected_without_reading_target
  - test_open_handle_boundary_is_checked_before_content_read
  - test_link_escape_branch_is_checked_without_host_symlink_privilege
  - test_bad_pattern_is_rejected
  - test_default_scan_never_traverses_unreadable_caches
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-023
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-023
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-023
      - key: TASK-RKG-023
        revision: 1
  record: '# PLAN-TASK-RKG-023


    Runbook vận hành local và regression cuối. Finding KPI và performance còn mở được chuyển nguyên, không
    đóng hộ.


    ## Thứ tự


    1. `README.md` — setup, index, serve, LLM, retention, troubleshooting. Kiểm: lệnh trong README chạy
    được trên suite hiện có.

    2. `regression` — suite hiện tại, ghi skip có lý do. Kiểm: TEST-RKG-FINAL-REGRESSION-001.


    ## Không làm


    - Không tuyên bố epic hay gate đã duyệt.

    - Không sửa finding của TASK-RKG-022 thành pass.'
---

# PLAN-TASK-RKG-023

Runbook vận hành local và regression cuối. Finding KPI và performance còn mở được chuyển nguyên, không đóng hộ.

## Thứ tự

1. `README.md` — setup, index, serve, LLM, retention, troubleshooting. Kiểm: lệnh trong README chạy được trên suite hiện có.
2. `regression` — suite hiện tại, ghi skip có lý do. Kiểm: TEST-RKG-FINAL-REGRESSION-001.

## Không làm

- Không tuyên bố epic hay gate đã duyệt.
- Không sửa finding của TASK-RKG-022 thành pass.

## Phạm vi code và kiểm chứng

- `README.md`

- `python -m pytest tests/integration/test_grounded_qa_live.py tests/integration/test_openrouter_live.py tests/integration/test_pilot_corpus.py tests/unit/test_local_source.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-023](../context/CTX-TASK-RKG-023.yaml). Kết quả triển khai: [DIARY-TASK-RKG-023](../diaries/DIARY-TASK-RKG-023.md).
