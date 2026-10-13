---
key: DIARY-TASK-RKG-018
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-018
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 4847c3d94a3b5c3375991fd41107ff0b8634ce8c
prior_evidence:
- evidence/context/CTX-TASK-RKG-018.yaml
- evidence/diaries/DIARY-TASK-RKG-018.md
- evidence/plans/PLAN-TASK-RKG-018.md
- evidence/plans/PLAN-TASK-RKG-018.md
- evidence/tests/TEST-RKG-CONVERSATION-STATE-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-018
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-018
    revision: 1
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-018
        revision: 5
      - key: FR-RKG-005
        revision: 7
      - key: CMP-RKG-CONVERSATION
        revision: 3
      - key: TBL-RKG-GRAPH
        revision: 9
      - key: API-RKG-CORE-v1
        revision: 9
      - key: NFR-RKG-REL-001
        revision: 8
      base_commit: 94558b78b6832e1abfc2a05fb77e56f2709efc4e
      code_tree: working-tree-file-hashes-below
      pins:
        cpython: 3.12.14
        kuzu: 0.11.3
  record: "# DIARY-TASK-RKG-018 — Conversation persistence and state\n\n## Thực hiện\n\n- Conversation\
    \ pin snapshot lúc tạo. Snapshot active mới không đổi pin cũ.\n  Đọc pin mất hoặc không `ready` trả\
    \ `snapshot_unavailable` và không trỏ sang\n  snapshot active.\n- `Turn.id` = `turn_` + SHA-256 hex\
    \ đủ 64 ký tự của\n  `conversation_id:client_request_id`. Cùng key khác body là\n  `conversation_conflict`;\
    \ cùng body replay, không gọi provider lần hai.\n- `expected_revision` dương nhưng không khớp revision\
    \ hiện tại là conflict.\n  Thiếu field, không phải số, hoặc số nhỏ hơn 1 là `invalid_turn_request`\n\
    \  và không tạo turn.\n- Turn `pending` chặn xóa (`conversation_busy`). Mở `Storage` chuyển pending\n\
    \  còn lại sang `interrupted`, giữ focus và history đã commit.\n- Provider lỗi ghi turn `failed`,\
    \ không đổi focus. Log `rkg.conversation`\n  chỉ có id, status và mã lỗi.\n- Cleanup xóa snapshot\
    \ không active, không có reader và không còn conversation\n  tham chiếu.\n\n## Kiểm chứng trên cây\
    \ mã hiện tại\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `uv run ruff check src tests` | pass |\n| `uv\
    \ run python -m pytest tests/ -q` | pass — 65 passed, 1 skipped |\n\nSHA-256 của file đã kiểm chứng:\n\
    \n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/conversations/__init__.py` | `9aa60b615d08702c55749cc3fde8751321ffc1ebdbd350c38d7cc0beea8fbe03`\
    \ |\n| `src/rkg/conversations/README.md` | `c41a3859fa48a2e17ce6fe4f9d46e8b2018d00748c2c7e779f2c59849abd5af1`\
    \ |\n| `src/rkg/conversations/identity.py` | `124415659436442bbf83f014535097f4c8b0894f9d09a1f6e27cb263a4e5ceb9`\
    \ |\n| `src/rkg/conversations/redaction.py` | `158127e52527b2a870263fa771f548138192d0800542144b61c1110aba436335`\
    \ |\n| `src/rkg/conversations/service.py` | `9562870be7d129b035108850d2b08548389a7e663e884774c88d9a99bd64682b`\
    \ |\n| `src/rkg/storage/README.md` | `6681a7fd5909279b78474b1c23db3bb83918f699f0e81dbfd0a2bfb01bd4819f`\
    \ |\n| `src/rkg/storage/__init__.py` | `6c9debc617e5c8c6b166c644414d1a55e058d8316e1638326eb8cf64d401a900`\
    \ |\n| `src/rkg/storage/connection.py` | `9ecc2406f510e4c922b21a8358a0403545d219f8a6ba990bd523cc2206f7c9f1`\
    \ |\n| `src/rkg/storage/conversations.py` | `a5e83f5c058eb0f0b7dcd42d3fcdb4fb669c28672cf435e858c58d41fc8e8ed7`\
    \ |\n| `src/rkg/storage/errors.py` | `5465d846751fbc8f5537453d9c9cdc3acd59612ade1a32acdcefecc15338ee7b`\
    \ |\n| `src/rkg/storage/oplog.py` | `aab0d0fc03fb5fcbbeeba7ab06147769de2f98f575be8e61bca3a72a9cda9a00`\
    \ |\n| `src/rkg/storage/records.py` | `ab7171acb19caaa7fe1d6bec0b95fd41d5e24731b5e8bacf5a8e31b98e623d0c`\
    \ |\n| `src/rkg/storage/snapshots.py` | `ba1936bad6d153b641fc7e54875284490b001934da29fb88b6dd1be1a1d2a399`\
    \ |\n| `src/rkg/storage/turns.py` | `02e7f2231a9f7efaeef891948ca758e3caaba66a51c0ca46e3a859b0a1526ac3`\
    \ |\n| `tests/integration/test_conversation_persistence.py` | `28c8ef1d15608390dd5f093e19696068dc07098f7e5f7a8ee68e274771264754`\
    \ |\n| `tests/unit/test_conversation_redaction.py` | `fc09e35ef2dbe6805a10b7c9c7b7156262486d44a0d5a2a3864884336b100b01`\
    \ |\n| `.aide/lifecycle/tasks/TASK-RKG-018.md` | `d44a6d920979ab4dbc1986e99d6aa298207420f83da8f324c00f42fc1942b661`\
    \ |\n\n## Deferred\n\n- HTTP routes and session checks → T-016 / T-021.\n- History window and grounded\
    \ answers → T-020.\n- AC-RKG-032 not executed in this task."
---

# DIARY-TASK-RKG-018

## Thực hiện

- Conversation pin snapshot lúc tạo. Snapshot active mới không đổi pin cũ.
  Đọc pin mất hoặc không `ready` trả `snapshot_unavailable` và không trỏ sang
  snapshot active.
- `Turn.id` = `turn_` + SHA-256 hex đủ 64 ký tự của
  `conversation_id:client_request_id`. Cùng key khác body là
  `conversation_conflict`; cùng body replay, không gọi provider lần hai.
- `expected_revision` dương nhưng không khớp revision hiện tại là conflict.
  Thiếu field, không phải số, hoặc số nhỏ hơn 1 là `invalid_turn_request`
  và không tạo turn.
- Turn `pending` chặn xóa (`conversation_busy`). Mở `Storage` chuyển pending
  còn lại sang `interrupted`, giữ focus và history đã commit.
- Provider lỗi ghi turn `failed`, không đổi focus. Log `rkg.conversation`
  chỉ có id, status và mã lỗi.
- Cleanup xóa snapshot không active, không có reader và không còn conversation
  tham chiếu.

## Kiểm chứng trên cây mã hiện tại

| Lệnh | Kết quả |
| --- | --- |
| `uv run ruff check src tests` | pass |
| `uv run python -m pytest tests/ -q` | pass — 65 passed, 1 skipped |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/conversations/__init__.py` | `9aa60b615d08702c55749cc3fde8751321ffc1ebdbd350c38d7cc0beea8fbe03` |
| `src/rkg/conversations/README.md` | `c41a3859fa48a2e17ce6fe4f9d46e8b2018d00748c2c7e779f2c59849abd5af1` |
| `src/rkg/conversations/identity.py` | `124415659436442bbf83f014535097f4c8b0894f9d09a1f6e27cb263a4e5ceb9` |
| `src/rkg/conversations/redaction.py` | `158127e52527b2a870263fa771f548138192d0800542144b61c1110aba436335` |
| `src/rkg/conversations/service.py` | `9562870be7d129b035108850d2b08548389a7e663e884774c88d9a99bd64682b` |
| `src/rkg/storage/README.md` | `6681a7fd5909279b78474b1c23db3bb83918f699f0e81dbfd0a2bfb01bd4819f` |
| `src/rkg/storage/__init__.py` | `6c9debc617e5c8c6b166c644414d1a55e058d8316e1638326eb8cf64d401a900` |
| `src/rkg/storage/connection.py` | `9ecc2406f510e4c922b21a8358a0403545d219f8a6ba990bd523cc2206f7c9f1` |
| `src/rkg/storage/conversations.py` | `a5e83f5c058eb0f0b7dcd42d3fcdb4fb669c28672cf435e858c58d41fc8e8ed7` |
| `src/rkg/storage/errors.py` | `5465d846751fbc8f5537453d9c9cdc3acd59612ade1a32acdcefecc15338ee7b` |
| `src/rkg/storage/oplog.py` | `aab0d0fc03fb5fcbbeeba7ab06147769de2f98f575be8e61bca3a72a9cda9a00` |
| `src/rkg/storage/records.py` | `ab7171acb19caaa7fe1d6bec0b95fd41d5e24731b5e8bacf5a8e31b98e623d0c` |
| `src/rkg/storage/snapshots.py` | `ba1936bad6d153b641fc7e54875284490b001934da29fb88b6dd1be1a1d2a399` |
| `src/rkg/storage/turns.py` | `02e7f2231a9f7efaeef891948ca758e3caaba66a51c0ca46e3a859b0a1526ac3` |
| `tests/integration/test_conversation_persistence.py` | `28c8ef1d15608390dd5f093e19696068dc07098f7e5f7a8ee68e274771264754` |
| `tests/unit/test_conversation_redaction.py` | `fc09e35ef2dbe6805a10b7c9c7b7156262486d44a0d5a2a3864884336b100b01` |
| `.aide/lifecycle/tasks/TASK-RKG-018.md` | `d44a6d920979ab4dbc1986e99d6aa298207420f83da8f324c00f42fc1942b661` |

## Deferred

- HTTP routes and session checks → T-016 / T-021.
- History window and grounded answers → T-020.
- AC-RKG-032 not executed in this task.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Persist conversation/turn, pin snapshot, enforce revision/client_request_id/idempotency/redaction; recover pending turn sau restart và chặn deletion khi busy.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

History-window AC-RKG-032 thuộc task 020; storage persistence không được nhận thay phần history-aware Q&A.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
