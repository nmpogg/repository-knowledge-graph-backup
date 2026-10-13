---
key: PLAN-TASK-RKG-024
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-024
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: 9557874b42a5aeca69e6f36e860382a99481d342
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-024.yaml
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
frontend_test_paths:
- frontend/src/client/live/liveClient.test.ts
- frontend/src/client/live/liveRoundtrip.test.ts
- frontend/src/client/live/mapWire.test.ts
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-024
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-024
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-024
      - key: TASK-RKG-024
        revision: 1
  record: '# PLAN-TASK-RKG-024


    Đổi client mock sang `/api/v1` mà giữ hành vi màn hình đã nghiệm thu trên mock.


    ## Thứ tự


    1. `API client` — cùng types với mock. Kiểm: onboarding, index, Explorer, repository lifecycle trên
    server.

    2. `job poll` — đúng Retry-After, hủy khi unmount. Kiểm: AC-RKG-061.


    ## Không làm


    - Không viết lại KnowledgeGraph.

    - Không thêm màn mới.'
---

# PLAN-TASK-RKG-024

Đổi client mock sang `/api/v1` mà giữ hành vi màn hình đã nghiệm thu trên mock.

## Thứ tự

1. `API client` — cùng types với mock. Kiểm: onboarding, index, Explorer, repository lifecycle trên server.
2. `job poll` — đúng Retry-After, hủy khi unmount. Kiểm: AC-RKG-061.

## Không làm

- Không viết lại KnowledgeGraph.
- Không thêm màn mới.

## Phạm vi code và kiểm chứng

- `frontend/src/client/index.ts`
- `frontend/src/client/live/liveClient.test.ts`
- `frontend/src/client/live/liveClient.ts`
- `frontend/src/client/live/liveRoundtrip.test.ts`
- `frontend/src/client/live/mapWire.test.ts`
- `frontend/src/client/live/mapWire.ts`
- `frontend/src/index.css`
- `frontend/src/pages/explorer/ExplorerPage.tsx`
- `frontend/src/pages/repositories/RepositoryCreatePage.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/vite-env.d.ts`
- `src/rkg/api/README.md`
- `src/rkg/api/__init__.py`
- `src/rkg/api/app.py`
- `tests/integration/test_core_api.py`

- `python -m pytest tests/integration/test_core_api.py -q`
- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-024](../context/CTX-TASK-RKG-024.yaml). Kết quả triển khai: [DIARY-TASK-RKG-024](../diaries/DIARY-TASK-RKG-024.md).
