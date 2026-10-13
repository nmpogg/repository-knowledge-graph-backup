---
key: PLAN-TASK-RKG-003
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-003
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 4ee8a54a47ecafe383baa0450040a7cc65e37914
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-003.yaml
verification_targets:
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
    key: PLAN-TASK-RKG-003
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-003
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-003
      - key: TASK-RKG-003
        revision: 1
  record: '# PLAN-TASK-RKG-003


    Dựng manifest từ repository local mà không import và không thực thi source.


    ## Thứ tự


    1. `src/rkg/ingestion/local.py` — canonicalize root, chặn path ngoài allowlist và link thoát root.
    Kiểm: fixture AC-RKG-051 không đọc đích và không sửa filesystem.

    2. `manifest builder` — liệt file được phép, hash, skip file quá lớn, fail khi quá max_files. Kiểm:
    AC-RKG-049 và AC-RKG-050.

    3. `import side-effect fixture` — scan không import module fixture. Kiểm: AC-RKG-001 không tạo side
    effect.


    ## Không làm


    - Không parse AST.

    - Không ghi database.

    - Không trả absolute host path trong lỗi.'
---

# PLAN-TASK-RKG-003

Dựng manifest từ repository local mà không import và không thực thi source.

## Thứ tự

1. `src/rkg/ingestion/local.py` — canonicalize root, chặn path ngoài allowlist và link thoát root. Kiểm: fixture AC-RKG-051 không đọc đích và không sửa filesystem.
2. `manifest builder` — liệt file được phép, hash, skip file quá lớn, fail khi quá max_files. Kiểm: AC-RKG-049 và AC-RKG-050.
3. `import side-effect fixture` — scan không import module fixture. Kiểm: AC-RKG-001 không tạo side effect.

## Không làm

- Không parse AST.
- Không ghi database.
- Không trả absolute host path trong lỗi.

## Phạm vi code và kiểm chứng

- `src/rkg/ingestion/README.md`
- `src/rkg/ingestion/__init__.py`
- `src/rkg/ingestion/local.py`
- `tests/unit/test_local_source.py`

- `python -m pytest tests/unit/test_local_source.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-003](../context/CTX-TASK-RKG-003.yaml). Kết quả triển khai: [DIARY-TASK-RKG-003](../diaries/DIARY-TASK-RKG-003.md).
