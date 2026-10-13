---
key: PLAN-TASK-RKG-016
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-016
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 20931a3d40889c60abf801498b9a1c698e2d19d7
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-016.yaml
verification_targets:
- path: tests/integration/test_core_api.py
  tests:
  - test_request_log_uses_route_template_without_query_or_payload
  - test_cors_reflects_loopback_origin_only
  - test_session_rejects_missing_token_bad_origin_and_remote_host
  - test_repository_crud_redacts_paths_and_guards_lifecycle
  - test_index_job_session_warnings_selection_and_single_writer
  - test_graph_reads_context_and_snapshot_guards
  - test_conversation_delete_is_busy_while_a_turn_is_pending
  - test_queued_job_advertises_retry_after
  - test_unreferenced_snapshot_and_repository_delete
  - test_repository_list_pages_without_overlap
  - test_serve_binds_fastapi_on_loopback
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-016
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-016
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-016
      - key: TASK-RKG-016
        revision: 1
  record: '# PLAN-TASK-RKG-016


    Serialize API v1 xuống service đã có. Transport không chứa extraction hay graph-write riêng.


    ## Thứ tự


    1. `src/rkg/api/catalog.py` — repository và snapshot CRUD, revision, redact locator. Kiểm: AC-RKG-066
    đến AC-RKG-072.

    2. `src/rkg/api/jobs.py` — submit và poll, Retry-After. Kiểm: AC-RKG-058, AC-RKG-061.

    3. `src/rkg/api/guard.py` — session, Origin, Host trước khi đọc source. Kiểm: 401 không lộ token.


    ## Không làm


    - Không đổi rule nghiệp vụ trong adapter.

    - Không thêm route conversation.

    - Không tự ký Contract Gate.'
---

# PLAN-TASK-RKG-016

Serialize API v1 xuống service đã có. Transport không chứa extraction hay graph-write riêng.

## Thứ tự

1. `src/rkg/api/catalog.py` — repository và snapshot CRUD, revision, redact locator. Kiểm: AC-RKG-066 đến AC-RKG-072.
2. `src/rkg/api/jobs.py` — submit và poll, Retry-After. Kiểm: AC-RKG-058, AC-RKG-061.
3. `src/rkg/api/guard.py` — session, Origin, Host trước khi đọc source. Kiểm: 401 không lộ token.

## Không làm

- Không đổi rule nghiệp vụ trong adapter.
- Không thêm route conversation.
- Không tự ký Contract Gate.

## Phạm vi code và kiểm chứng

- `pyproject.toml`
- `src/rkg/api/README.md`
- `src/rkg/api/__init__.py`
- `src/rkg/api/app.py`
- `src/rkg/api/catalog.py`
- `src/rkg/api/errors.py`
- `src/rkg/api/guard.py`
- `src/rkg/api/jobs.py`
- `src/rkg/api/serialize.py`
- `src/rkg/cli/__init__.py`
- `src/rkg/conversations/README.md`
- `src/rkg/domain/README.md`
- `src/rkg/graph/README.md`
- `src/rkg/jobs/__init__.py`
- `src/rkg/jobs/coordinator.py`
- `tests/integration/test_core_api.py`
- `uv.lock`

- `python -m pytest tests/integration/test_core_api.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-016](../context/CTX-TASK-RKG-016.yaml). Kết quả triển khai: [DIARY-TASK-RKG-016](../diaries/DIARY-TASK-RKG-016.md).
