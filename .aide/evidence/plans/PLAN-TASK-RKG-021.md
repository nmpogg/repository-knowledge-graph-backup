---
key: PLAN-TASK-RKG-021
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-021
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: d94aff5443c57070842fa4984bdadc99920bc75a
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-021.yaml
verification_targets:
- path: tests/integration/test_conversation_api.py
  tests:
  - test_session_blocks_create_and_turn_before_provider
  - test_create_list_followup_and_ordered_clarification
  - test_required_fields_conflict_timeout_and_redaction
  - test_injection_and_history_window
  - test_lost_snapshot_stays_pinned
  - test_indexed_local_fixture_citation_uses_that_snapshot
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
- frontend/src/pages/conversations/ConversationPage.test.tsx
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-021
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-021
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-021
      - key: TASK-RKG-021
        revision: 1
  record: '# PLAN-TASK-RKG-021


    Lộ conversation qua API và UI trên snapshot thật, không đổi service grounded.


    ## Thứ tự


    1. `src/rkg/api/conversations.py` — session, revision, client_request_id. Kiểm: AC-RKG-041, AC-RKG-059.

    2. `frontend conversation` — citation, escape markdown, focus order. Kiểm: AC-RKG-046, AC-RKG-047.


    ## Không làm


    - Không đổi rubric trả lời.

    - Không stream token.'
---

# PLAN-TASK-RKG-021

Lộ conversation qua API và UI trên snapshot thật, không đổi service grounded.

## Thứ tự

1. `src/rkg/api/conversations.py` — session, revision, client_request_id. Kiểm: AC-RKG-041, AC-RKG-059.
2. `frontend conversation` — citation, escape markdown, focus order. Kiểm: AC-RKG-046, AC-RKG-047.

## Không làm

- Không đổi rubric trả lời.
- Không stream token.

## Phạm vi code và kiểm chứng

- `README.md`
- `frontend/src/App.tsx`
- `frontend/src/client/live/liveClient.ts`
- `frontend/src/client/live/mapWire.ts`
- `frontend/src/client/mock/mockClient.ts`
- `frontend/src/components/ui/ConfirmDialog.tsx`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/vi.ts`
- `frontend/src/index.css`
- `frontend/src/pages/conversations/ConversationPage.test.tsx`
- `frontend/src/pages/conversations/ConversationPage.tsx`
- `frontend/src/pages/conversations/ConversationsPage.tsx`
- `frontend/src/pages/repositories/RepositoryCreatePage.tsx`
- `frontend/src/types/api.ts`
- `src/rkg/api/README.md`
- `src/rkg/api/__init__.py`
- `src/rkg/api/app.py`
- `src/rkg/api/conversations.py`
- `src/rkg/api/errors.py`
- `src/rkg/conversations/README.md`
- `src/rkg/conversations/__init__.py`
- `src/rkg/conversations/service.py`
- `src/rkg/storage/connection.py`
- `src/rkg/storage/conversations.py`
- `tests/integration/test_conversation_api.py`

- `python -m pytest tests/integration/test_conversation_api.py tests/integration/test_core_api.py -q`
- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-021](../context/CTX-TASK-RKG-021.yaml). Kết quả triển khai: [DIARY-TASK-RKG-021](../diaries/DIARY-TASK-RKG-021.md).
