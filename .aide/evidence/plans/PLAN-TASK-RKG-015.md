---
key: PLAN-TASK-RKG-015
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-015
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 668df4b4d749c7935de7b9fe9472fad7a3a42d1a
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-015.yaml
verification_targets:
- path: tests/integration/test_index_coordinator.py
  tests:
  - test_reindex_failure_and_recovery
  - test_warnings_and_global_busy
  - test_cli_repository_and_index
  - test_fastapi_selection_and_binding
  - test_unknown_version_factory_publishes_routes_and_warning
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-015
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-015
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-015
      - key: TASK-RKG-015
        revision: 1
  record: '# PLAN-TASK-RKG-015


    Ghép ingestion, detection, extract và publication thành một job. CLI cùng contract với API.


    ## Thứ tự


    1. `src/rkg/jobs/coordinator.py` — một job, 409 khi bận, recover job đứt. Kiểm: AC-RKG-034.

    2. `scan report` — số file, entity, warning, không trạng thái partial. Kiểm: AC-RKG-012, AC-RKG-038.

    3. `CLI index/serve` — exit 0/1, bind 127.0.0.1, một worker. Kiểm: AC-RKG-055.


    ## Không làm


    - Không mở HTTP server đầy đủ (TASK-RKG-016).

    - Không đo benchmark AC-RKG-039 (TASK-RKG-022).'
---

# PLAN-TASK-RKG-015

Ghép ingestion, detection, extract và publication thành một job. CLI cùng contract với API.

## Thứ tự

1. `src/rkg/jobs/coordinator.py` — một job, 409 khi bận, recover job đứt. Kiểm: AC-RKG-034.
2. `scan report` — số file, entity, warning, không trạng thái partial. Kiểm: AC-RKG-012, AC-RKG-038.
3. `CLI index/serve` — exit 0/1, bind 127.0.0.1, một worker. Kiểm: AC-RKG-055.

## Không làm

- Không mở HTTP server đầy đủ (TASK-RKG-016).
- Không đo benchmark AC-RKG-039 (TASK-RKG-022).

## Phạm vi code và kiểm chứng

- `pyproject.toml`
- `src/rkg/__main__.py`
- `src/rkg/adapters/fastapi_framework.py`
- `src/rkg/cli/__init__.py`
- `src/rkg/jobs/__init__.py`
- `src/rkg/jobs/coordinator.py`
- `tests/integration/test_index_coordinator.py`

- `python -m pytest tests/integration/test_index_coordinator.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-015](../context/CTX-TASK-RKG-015.yaml). Kết quả triển khai: [DIARY-TASK-RKG-015](../diaries/DIARY-TASK-RKG-015.md).
