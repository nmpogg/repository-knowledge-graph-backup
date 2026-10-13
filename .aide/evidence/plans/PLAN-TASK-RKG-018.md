---
key: PLAN-TASK-RKG-018
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-018
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 4847c3d94a3b5c3375991fd41107ff0b8634ce8c
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-018.yaml
verification_targets:
- path: tests/integration/test_conversation_persistence.py
  tests:
  - test_ac030_history_survives_restart_and_focus_is_isolated
  - test_ac031_old_conversation_stays_pinned_when_active_moves
  - test_ac033_conflict_idempotency_recovery_and_failed_focus
  - test_ac044_cleanup_keeps_guards_and_lost_snapshot_stays_pinned
  - test_ac045_pending_delete_is_busy_and_other_history_remains
  - test_ac059_missing_or_malformed_fields_do_not_mutate
  - test_ac064_redacts_store_and_omits_transcript_from_logs
- path: tests/unit/test_conversation_redaction.py
  tests:
  - test_turn_id_is_full_sha256
  - test_same_body_hash_is_stable_and_distinct
  - test_redaction_removes_forbidden_fragments_and_keeps_prose
  - test_json_redaction_drops_reasoning_and_secrets
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-018
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-018
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-018
      - key: TASK-RKG-018
        revision: 1
  record: |-
    # PLAN-TASK-RKG-018

    Lưu conversation trên cùng DB, pin snapshot, idempotency theo client_request_id.

    ## Thứ tự

    1. `conversation store` — persist, isolate, delete guard. Kiểm: AC-RKG-030, AC-RKG-045.
    2. `pin và window` — snapshot cũ không bị kéo; history_truncated. Kiểm: AC-RKG-031, AC-RKG-032.
    3. `idempotency` — cùng client_request_id không nhân turn. Kiểm: AC-RKG-033, AC-RKG-044.

    ## Không làm

    - Không gọi LLM.
    - Không mở writer ngoài single-writer process.
- revision: 2
  metadata:
    key: PLAN-TASK-RKG-018
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-018
    revision: 2
    captured_at: 2026-10-02
    captured_against:
      artifacts:
      - key: PLAN-TASK-RKG-018
        revision: 1
        path: evidence/plans/PLAN-TASK-RKG-018.md
      - key: TASK-RKG-018
        revision: 7
      - key: STORY-RKG-012
        revision: 2
      - key: STORY-RKG-013
        revision: 2
      - key: TASK-RKG-020
        revision: 8
    prior_plan: PLAN-TASK-RKG-018.md
  record: |-
    # PLAN-TASK-RKG-018 revision 2

    Current relationship for history window. Revision 1 of this plan is kept in
    `PLAN-TASK-RKG-018.md` and is not edited. That revision checked `AC-RKG-032`
    on this task. The current AC belongs to `STORY-RKG-013` and is checked by
    `TASK-RKG-020`.

    ## Thứ tự

    1. `conversation store` — persist, isolate, delete guard. Kiểm: AC-RKG-030, AC-RKG-045.
    2. `pin` — snapshot cũ không bị kéo. Kiểm: AC-RKG-031.
    3. `idempotency` — cùng client_request_id không nhân turn. Kiểm: AC-RKG-033, AC-RKG-044.

    ## Không làm

    - Không kiểm `AC-RKG-032` ở task này. History window thuộc `TASK-RKG-020`.
    - Không gọi LLM.
    - Không mở writer ngoài single-writer process.
    - Không sửa `PLAN-TASK-RKG-018.md`.
---

# PLAN-TASK-RKG-018

Lưu conversation trên cùng DB, pin snapshot, idempotency theo client_request_id.

## Thứ tự

1. `conversation store` — persist, isolate, delete guard. Kiểm: AC-RKG-030, AC-RKG-045.
2. `pin và window` — snapshot cũ không bị kéo; history_truncated. Kiểm: AC-RKG-031, AC-RKG-032.
3. `idempotency` — cùng client_request_id không nhân turn. Kiểm: AC-RKG-033, AC-RKG-044.

## Không làm

- Không gọi LLM.
- Không mở writer ngoài single-writer process.

## Phạm vi code và kiểm chứng

- `src/rkg/conversations/README.md`
- `src/rkg/conversations/__init__.py`
- `src/rkg/conversations/identity.py`
- `src/rkg/conversations/redaction.py`
- `src/rkg/conversations/service.py`
- `src/rkg/storage/README.md`
- `src/rkg/storage/__init__.py`
- `src/rkg/storage/connection.py`
- `src/rkg/storage/conversations.py`
- `src/rkg/storage/errors.py`
- `src/rkg/storage/oplog.py`
- `src/rkg/storage/records.py`
- `src/rkg/storage/snapshots.py`
- `src/rkg/storage/turns.py`
- `tests/integration/test_conversation_persistence.py`
- `tests/unit/test_conversation_redaction.py`

- `python -m pytest tests/integration/test_conversation_persistence.py tests/unit/test_conversation_redaction.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-018](../context/CTX-TASK-RKG-018.yaml). Kết quả triển khai: [DIARY-TASK-RKG-018](../diaries/DIARY-TASK-RKG-018.md).
