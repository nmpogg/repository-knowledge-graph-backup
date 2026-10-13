---
key: PLAN-TASK-RKG-028
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-028
revision: 3
plan_date: '2026-10-01'
date_basis:
  commit: 7b24db7773298fd2c548b76f3cd3ac46ca24cc62
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-028.yaml
verification_targets:
- path: tests/conformance/test_fastapi_framework.py
  tests:
  - test_factory_literal_loop_and_empty_path
  - test_ambiguous_factories_do_not_guess_routes
  - test_dynamic_loop_is_diagnostic_and_unattached_routes_are_not_published
  - test_empty_path_without_effective_prefix_is_rejected
  - test_direct_nested_router_multi_method_and_unattached_router
  - test_declared_dependencies_across_wiring_layers
  - test_dynamic_routes_duplicate_binding_and_local_shadow_are_conservative
  - test_direct_registration_and_router_cycle
  - test_registered_adapter_is_selected_with_verified_version
  - test_multiple_apps_require_explicit_entrypoint
- path: tests/integration/test_index_coordinator.py
  tests:
  - test_reindex_failure_and_recovery
  - test_warnings_and_global_busy
  - test_cli_repository_and_index
  - test_fastapi_selection_and_binding
  - test_unknown_version_factory_publishes_routes_and_warning
- path: tests/integration/test_index_language_partition.py
  tests:
  - test_python_only_repository_still_builds_the_same_graph
  - test_other_language_runs_and_python_does_not_parse
  - test_two_languages_merge_into_one_snapshot
  - test_companion_uses_only_the_parent_language_portion
  - test_unregistered_extension_succeeds_without_language_nodes
  - test_duplicate_language_extension_fails_the_job
  - test_shared_directory_is_built_once_for_two_languages
- path: tests/unit/test_technology_detection.py
  tests:
  - test_declared_only_and_version_states
  - test_fastapi_unknown_version_extracts_without_supported_claim
  - test_app_candidates_override_and_reindex_selection
  - test_single_app_auto_select_and_unresolved
  - test_multiple_deep_adapters_and_local_shadow
  - test_new_detector_and_adapter_need_no_coordinator_change
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-028
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-028
    captured_at: 2026-10-01
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-028
      - key: TASK-RKG-028
        revision: 1
  record: '# PLAN-TASK-RKG-028


    Lấp bốn lỗ static đã được xác nhận, không chạy Python để đoán route.


    ## Thứ tự


    1. `version unverified` — opt-in FastAPI, version không tương thích vẫn bị chặn. Kiểm: AC-RKG-020.

    2. `local factory và literal loop` — giữ location, diagnostic khi mơ hồ. Kiểm: AC-RKG-004, AC-RKG-040,
    AC-RKG-052.

    3. `empty path` — kế thừa prefix, không thêm slash. Kiểm: regression route.


    ## Không làm


    - Không opt-in hộ adapter khác.

    - Không đổi schema.

    - Không restart server người dùng đang chạy.'
---

# PLAN-TASK-RKG-028

Lấp bốn lỗ static đã được xác nhận, không chạy Python để đoán route.

## Thứ tự

1. `version unverified` — opt-in FastAPI, version không tương thích vẫn bị chặn. Kiểm: AC-RKG-020.
2. `local factory và literal loop` — giữ location, diagnostic khi mơ hồ. Kiểm: AC-RKG-004, AC-RKG-040, AC-RKG-052.
3. `empty path` — kế thừa prefix, không thêm slash. Kiểm: regression route.

## Không làm

- Không opt-in hộ adapter khác.
- Không đổi schema.
- Không restart server người dùng đang chạy.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/fastapi_framework.py`
- `src/rkg/adapters/fastapi_static.py`
- `src/rkg/adapters/registry.py`
- `src/rkg/detection/README.md`
- `src/rkg/detection/fastapi.py`
- `src/rkg/detection/selection.py`
- `src/rkg/jobs/coordinator.py`
- `tests/conformance/test_fastapi_framework.py`
- `tests/integration/test_index_coordinator.py`
- `tests/integration/test_index_language_partition.py`
- `tests/unit/test_technology_detection.py`

- `python -m pytest tests/conformance/test_fastapi_framework.py tests/integration/test_index_coordinator.py tests/integration/test_index_language_partition.py tests/unit/test_technology_detection.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-028](../context/CTX-TASK-RKG-028.yaml). Kết quả triển khai: [DIARY-TASK-RKG-028](../diaries/DIARY-TASK-RKG-028.md).
