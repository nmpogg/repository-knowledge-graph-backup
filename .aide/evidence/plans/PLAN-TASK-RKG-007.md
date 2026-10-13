---
key: PLAN-TASK-RKG-007
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-007
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 4e902ebd2e86dbfe8a7afd8e491ecaf25a73168e
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-007.yaml
verification_targets:
- path: tests/conformance/test_python_metadata.py
  tests:
  - test_declared_lock_and_import_provenance
  - test_local_shadow_and_unknown_distribution_are_not_guessed
  - test_requirements_include_cycle_and_dynamic_metadata
  - test_poetry_groups_and_group_include_cycle
  - test_nested_callable_usage_belongs_to_inner_callable
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-007
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-007
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-007
      - key: TASK-RKG-007
        revision: 1
  record: '# PLAN-TASK-RKG-007


    Inventory dependency từ manifest và usage import, giữ provenance, không suy version từ môi trường
    analyzer.


    ## Thứ tự


    1. `python metadata adapter` — declared, lock, marker, usage import. Kiểm: AC-RKG-022 golden.


    ## Không làm


    - Không dựng external call graph.

    - Không gọi network để tra package.'
---

# PLAN-TASK-RKG-007

Inventory dependency từ manifest và usage import, giữ provenance, không suy version từ môi trường analyzer.

## Thứ tự

1. `python metadata adapter` — declared, lock, marker, usage import. Kiểm: AC-RKG-022 golden.

## Không làm

- Không dựng external call graph.
- Không gọi network để tra package.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/python_language.py`
- `src/rkg/adapters/python_metadata.py`
- `tests/conformance/test_python_metadata.py`

- `python -m pytest tests/conformance/test_python_metadata.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-007](../context/CTX-TASK-RKG-007.yaml). Kết quả triển khai: [DIARY-TASK-RKG-007](../diaries/DIARY-TASK-RKG-007.md).
