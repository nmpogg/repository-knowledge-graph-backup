---
key: PLAN-TASK-RKG-012
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-012
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 50eacb32b975117c149153fc932418bf2a7522de
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-012.yaml
verification_targets:
- path: tests/conformance/test_python_config.py
  tests:
  - test_environment_and_settings_keys_omit_sentinels
  - test_http_literal_origins_drop_sensitive_url_parts
  - test_shadowed_or_dynamic_config_is_not_guessed
- path: tests/conformance/test_python_metadata.py
  tests:
  - test_declared_lock_and_import_provenance
  - test_local_shadow_and_unknown_distribution_are_not_guessed
  - test_requirements_include_cycle_and_dynamic_metadata
  - test_poetry_groups_and_group_include_cycle
  - test_nested_callable_usage_belongs_to_inner_callable
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
- path: tests/integration/test_config_http_publish.py
  tests:
  - test_published_graph_context_and_log_omit_configuration_values
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-012
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-012
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-012
      - key: TASK-RKG-012
        revision: 1
  record: '# PLAN-TASK-RKG-012


    Key cấu hình và origin HTTP literal, không giữ secret, query hay payload.


    ## Thứ tự


    1. `config extraction` — key và depends_on users, sentinel vắng mặt ở output. Kiểm: AC-RKG-016.

    2. `http origins` — dedupe literal origin. Kiểm: AC-RKG-023.


    ## Không làm


    - Không đọc giá trị env vào graph.

    - Không resolve URL động thành origin.'
---

# PLAN-TASK-RKG-012

Key cấu hình và origin HTTP literal, không giữ secret, query hay payload.

## Thứ tự

1. `config extraction` — key và depends_on users, sentinel vắng mặt ở output. Kiểm: AC-RKG-016.
2. `http origins` — dedupe literal origin. Kiểm: AC-RKG-023.

## Không làm

- Không đọc giá trị env vào graph.
- Không resolve URL động thành origin.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/python_config.py`
- `src/rkg/adapters/python_language.py`
- `src/rkg/domain/README.md`
- `tests/conformance/test_python_config.py`
- `tests/integration/test_config_http_publish.py`

- `python -m pytest tests/conformance/test_python_config.py tests/conformance/test_python_metadata.py tests/conformance/test_python_resolution.py tests/integration/test_config_http_publish.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-012](../context/CTX-TASK-RKG-012.yaml). Kết quả triển khai: [DIARY-TASK-RKG-012](../diaries/DIARY-TASK-RKG-012.md).
