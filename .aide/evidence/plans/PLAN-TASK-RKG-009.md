---
key: PLAN-TASK-RKG-009
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-009
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: ca69624fb4f810955f38ffa3111d5873bfa743c2
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-009.yaml
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
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-009
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-009
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-009
      - key: TASK-RKG-009
        revision: 1
  record: '# PLAN-TASK-RKG-009


    Endpoint exposed và depends_on theo profile đã đăng ký. Router chưa gắn thì không thành endpoint.


    ## Thứ tự


    1. `fastapi adapter` — method, full path, handler, registration chain. Kiểm: AC-RKG-004.

    2. `dependency wiring` — depends_on đúng chiều. Kiểm: AC-RKG-005.


    ## Không làm


    - Không chạy app FastAPI.

    - Không biến declared dependency thành calls.'
---

# PLAN-TASK-RKG-009

Endpoint exposed và depends_on theo profile đã đăng ký. Router chưa gắn thì không thành endpoint.

## Thứ tự

1. `fastapi adapter` — method, full path, handler, registration chain. Kiểm: AC-RKG-004.
2. `dependency wiring` — depends_on đúng chiều. Kiểm: AC-RKG-005.

## Không làm

- Không chạy app FastAPI.
- Không biến declared dependency thành calls.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/__init__.py`
- `src/rkg/adapters/fastapi_framework.py`
- `tests/conformance/test_fastapi_framework.py`

- `python -m pytest tests/conformance/test_fastapi_framework.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-009](../context/CTX-TASK-RKG-009.yaml). Kết quả triển khai: [DIARY-TASK-RKG-009](../diaries/DIARY-TASK-RKG-009.md).
