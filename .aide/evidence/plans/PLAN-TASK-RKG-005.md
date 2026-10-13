---
key: PLAN-TASK-RKG-005
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-005
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 49e89097ee167403c0662ec85034a81f99c8aa4d
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-005.yaml
verification_targets:
- path: tests/conformance/test_python_language.py
  tests:
  - test_source_structure_matches_golden
  - test_syntax_error_is_isolated_and_path_safe
  - test_no_guessed_relationships_and_duplicate_binding
  - test_control_blocks_keep_lexical_owner_and_duplicate_subtree_is_skipped
  - test_python_adapter_passes_shared_conformance
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-005
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-005
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-005
      - key: TASK-RKG-005
        revision: 1
  record: '# PLAN-TASK-RKG-005


    Parse Python 3.12 thành structured unit và scope, không regex toàn file, không chạy source.


    ## Thứ tự


    1. `python language adapter` — SourceUnit, type, callable, member callable và containment. Kiểm: golden
    AC-RKG-002.

    2. `syntax errors` — diagnostic relative path, file khác vẫn extract. Kiểm: AC-RKG-035.


    ## Không làm


    - Không resolve import/call (TASK-RKG-006).

    - Không extract framework.'
---

# PLAN-TASK-RKG-005

Parse Python 3.12 thành structured unit và scope, không regex toàn file, không chạy source.

## Thứ tự

1. `python language adapter` — SourceUnit, type, callable, member callable và containment. Kiểm: golden AC-RKG-002.
2. `syntax errors` — diagnostic relative path, file khác vẫn extract. Kiểm: AC-RKG-035.

## Không làm

- Không resolve import/call (TASK-RKG-006).
- Không extract framework.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/__init__.py`
- `src/rkg/adapters/python_language.py`
- `tests/conformance/test_python_language.py`
- `tests/fixtures/python_structure/pkg/orders.py`

- `python -m pytest tests/conformance/test_python_language.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-005](../context/CTX-TASK-RKG-005.yaml). Kết quả triển khai: [DIARY-TASK-RKG-005](../diaries/DIARY-TASK-RKG-005.md).
