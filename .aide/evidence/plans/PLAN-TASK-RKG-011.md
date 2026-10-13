---
key: PLAN-TASK-RKG-011
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-011
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 8e9882d26a825c906fe880086ab362c7e1d77250
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-011.yaml
verification_targets:
- path: tests/conformance/test_aiokafka_messaging.py
  tests:
  - test_literal_constant_and_shared_channel
  - test_dynamic_topic_and_unscoped_call_do_not_emit_edges
  - test_unresolved_receiver_and_repeated_binding_do_not_emit
  - test_local_aiokafka_module_is_not_analyzed
  - test_lock_selects_adapter_without_entrypoint
- path: tests/conformance/test_sqlalchemy_data.py
  tests:
  - test_declarative_identity_does_not_merge_names_or_guess
  - test_reads_and_writes_follow_executed_patterns
  - test_local_sqlalchemy_module_is_not_analyzed
  - test_lock_selects_adapter_without_entrypoint
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-011
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-011
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-011
      - key: TASK-RKG-011
        revision: 1
  record: '# PLAN-TASK-RKG-011


    Publisher và consumer nối MessageChannel khi topic là literal hoặc hằng module.


    ## Thứ tự


    1. `aiokafka adapter` — channel + namespace. Kiểm: AC-RKG-015.


    ## Không làm


    - Không lưu payload.

    - Không nối topic động.'
---

# PLAN-TASK-RKG-011

Publisher và consumer nối MessageChannel khi topic là literal hoặc hằng module.

## Thứ tự

1. `aiokafka adapter` — channel + namespace. Kiểm: AC-RKG-015.

## Không làm

- Không lưu payload.
- Không nối topic động.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/__init__.py`
- `src/rkg/adapters/aiokafka_messaging.py`
- `src/rkg/adapters/sqlalchemy_data.py`
- `src/rkg/detection/README.md`
- `tests/conformance/test_aiokafka_messaging.py`
- `tests/conformance/test_sqlalchemy_data.py`

- `python -m pytest tests/conformance/test_aiokafka_messaging.py tests/conformance/test_sqlalchemy_data.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-011](../context/CTX-TASK-RKG-011.yaml). Kết quả triển khai: [DIARY-TASK-RKG-011](../diaries/DIARY-TASK-RKG-011.md).
