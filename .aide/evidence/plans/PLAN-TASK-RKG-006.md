---
key: PLAN-TASK-RKG-006
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-006
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: c91e4d2ff0b249848e0d39f26bbe5b161b95abb5
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-006.yaml
verification_targets:
- path: tests/conformance/test_python_language.py
  tests:
  - test_source_structure_matches_golden
  - test_syntax_error_is_isolated_and_path_safe
  - test_no_guessed_relationships_and_duplicate_binding
  - test_control_blocks_keep_lexical_owner_and_duplicate_subtree_is_skipped
  - test_python_adapter_passes_shared_conformance
- path: tests/conformance/test_python_resolution.py
  tests:
  - test_direct_alias_relative_imports_and_await_calls
  - test_shadowing_star_import_dynamic_dispatch_and_constructor_are_not_calls
  - test_unique_instance_method_call_and_reassignment_is_not_guessed
  - test_local_receivers_self_fields_annotations_and_inheritance
  - test_conflicting_parameter_types_and_reassigned_fields_are_not_guessed
  - test_direct_bases_and_explicit_abstraction_only
  - test_local_module_shadows_distribution_name_without_external_fact
  - test_reassigned_import_binding_does_not_create_call
  - test_local_abc_name_does_not_mark_type_as_abstract
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-006
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-006
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-006
      - key: TASK-RKG-006
        revision: 1
  record: '# PLAN-TASK-RKG-006


    Nối import, call và quan hệ class khi có đúng một target. Còn lại là diagnostic.


    ## Thứ tự


    1. `import resolution` — internal symbol hoặc ExternalDependency. Kiểm: AC-RKG-003.

    2. `call resolution` — calls đúng hướng, evidence tại call site. Kiểm: AC-RKG-048 và AC-RKG-006.

    3. `class relations` — implements chỉ abstraction khai báo; inherits_from là base trực tiếp. Kiểm:
    AC-RKG-017.

    4. `validator` — mọi edge có evidence. Kiểm: AC-RKG-007.


    ## Không làm


    - Không đoán dynamic dispatch, star import, hoặc binding bị che.

    - Không tạo fact bằng LLM.'
---

# PLAN-TASK-RKG-006

Nối import, call và quan hệ class khi có đúng một target. Còn lại là diagnostic.

## Thứ tự

1. `import resolution` — internal symbol hoặc ExternalDependency. Kiểm: AC-RKG-003.
2. `call resolution` — calls đúng hướng, evidence tại call site. Kiểm: AC-RKG-048 và AC-RKG-006.
3. `class relations` — implements chỉ abstraction khai báo; inherits_from là base trực tiếp. Kiểm: AC-RKG-017.
4. `validator` — mọi edge có evidence. Kiểm: AC-RKG-007.

## Không làm

- Không đoán dynamic dispatch, star import, hoặc binding bị che.
- Không tạo fact bằng LLM.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/python_language.py`
- `src/rkg/adapters/python_resolution.py`
- `tests/conformance/test_python_language.py`
- `tests/conformance/test_python_resolution.py`

- `python -m pytest tests/conformance/test_python_language.py tests/conformance/test_python_resolution.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-006](../context/CTX-TASK-RKG-006.yaml). Kết quả triển khai: [DIARY-TASK-RKG-006](../diaries/DIARY-TASK-RKG-006.md).
