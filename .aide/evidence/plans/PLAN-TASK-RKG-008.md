---
key: PLAN-TASK-RKG-008
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-008
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 51cede902a688529ebcd6ec164af7b3a86d826a0
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-008.yaml
verification_targets:
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
    key: PLAN-TASK-RKG-008
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-008
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-008
      - key: TASK-RKG-008
        revision: 1
  record: '# PLAN-TASK-RKG-008


    Detection và chọn app/adapter theo evidence. Không tự chọn khi có nhiều entrypoint.


    ## Thứ tự


    1. `src/rkg/detection/selection.py` — support state và app candidates. Kiểm: AC-RKG-020, AC-RKG-040,
    AC-RKG-052, AC-RKG-065.

    2. `negative fixtures` — shadowing và hai technology cùng hệ. Kiểm: AC-RKG-021, AC-RKG-053.


    ## Không làm


    - Không mở UI.

    - Không coi detected_only là deep-supported.'
---

# PLAN-TASK-RKG-008

Detection và chọn app/adapter theo evidence. Không tự chọn khi có nhiều entrypoint.

## Thứ tự

1. `src/rkg/detection/selection.py` — support state và app candidates. Kiểm: AC-RKG-020, AC-RKG-040, AC-RKG-052, AC-RKG-065.
2. `negative fixtures` — shadowing và hai technology cùng hệ. Kiểm: AC-RKG-021, AC-RKG-053.

## Không làm

- Không mở UI.
- Không coi detected_only là deep-supported.

## Phạm vi code và kiểm chứng

- `src/rkg/detection/README.md`
- `src/rkg/detection/__init__.py`
- `src/rkg/detection/contracts.py`
- `src/rkg/detection/fastapi.py`
- `src/rkg/detection/python_imports.py`
- `src/rkg/detection/selection.py`
- `tests/unit/test_technology_detection.py`

- `python -m pytest tests/unit/test_technology_detection.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-008](../context/CTX-TASK-RKG-008.yaml). Kết quả triển khai: [DIARY-TASK-RKG-008](../diaries/DIARY-TASK-RKG-008.md).
