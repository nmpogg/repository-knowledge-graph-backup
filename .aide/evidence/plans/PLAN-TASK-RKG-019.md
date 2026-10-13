---
key: PLAN-TASK-RKG-019
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-019
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: ca850045d9b20b7209a5c61ae9044598c41564d4
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-019.yaml
verification_targets:
- path: tests/integration/test_openrouter_live.py
  tests:
  - test_openrouter_live_structured_response
- path: tests/unit/test_llm_provider.py
  tests:
  - test_mock_enforces_schema_and_shared_model_query_limits
  - test_mock_rejects_nonconforming_output
  - test_preflight_rejects_oversize_input_without_calling_provider
  - test_openrouter_sends_structured_request_and_handles_missing_usage
  - test_openrouter_model_can_be_selected_from_environment
  - test_openrouter_disabled_does_not_call_transport
  - test_timeout_is_per_turn_and_raw_transport_error_is_hidden
  - test_reported_output_usage_cannot_exceed_budget
  - test_socket_timeout_maps_to_stable_code
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-019
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-019
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-019
      - key: TASK-RKG-019
        revision: 1
  record: '# PLAN-TASK-RKG-019


    Interface provider và adapter OpenRouter. Secret không vào graph, browser payload hay log.


    ## Thứ tự


    1. `src/rkg/llm/provider.py` — timeout, token budget, schema. Kiểm: vượt giới hạn thì lỗi trước khi
    ghi focus.

    2. `src/rkg/llm/openrouter.py` — adapter thật, secret chỉ từ env. Kiểm: live eval không in credential.

    3. `redaction` — log không chứa transcript. Kiểm: AC-RKG-064.


    ## Không làm


    - Không map HTTP conversation ở đây (TASK-RKG-021).

    - Không ghi graph fact từ output model.

    - Không để credential trong repo.'
---

# PLAN-TASK-RKG-019

Interface provider và adapter OpenRouter. Secret không vào graph, browser payload hay log.

## Thứ tự

1. `src/rkg/llm/provider.py` — timeout, token budget, schema. Kiểm: vượt giới hạn thì lỗi trước khi ghi focus.
2. `src/rkg/llm/openrouter.py` — adapter thật, secret chỉ từ env. Kiểm: live eval không in credential.
3. `redaction` — log không chứa transcript. Kiểm: AC-RKG-064.

## Không làm

- Không map HTTP conversation ở đây (TASK-RKG-021).
- Không ghi graph fact từ output model.
- Không để credential trong repo.

## Phạm vi code và kiểm chứng

- `pyproject.toml`
- `src/rkg/llm/README.md`
- `src/rkg/llm/__init__.py`
- `src/rkg/llm/data/o200k_base.tiktoken`
- `src/rkg/llm/mock.py`
- `src/rkg/llm/openrouter.py`
- `src/rkg/llm/provider.py`
- `tests/integration/test_openrouter_live.py`
- `tests/unit/test_llm_provider.py`
- `uv.lock`

- `python -m pytest tests/integration/test_openrouter_live.py tests/unit/test_llm_provider.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-019](../context/CTX-TASK-RKG-019.yaml). Kết quả triển khai: [DIARY-TASK-RKG-019](../diaries/DIARY-TASK-RKG-019.md).
