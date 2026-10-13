---
key: DIARY-TASK-RKG-021
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-021
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - d94aff5443c57070842fa4984bdadc99920bc75a
prior_evidence:
- evidence/context/CTX-TASK-RKG-021.yaml
- evidence/diaries/DIARY-TASK-RKG-021.md
- evidence/plans/PLAN-TASK-RKG-021.md
- evidence/tests/TEST-RKG-CONVERSATION-API-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-021
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-021
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-021
        revision: 5
      - key: FR-RKG-005
        revision: 7
      - key: API-RKG-CORE-v1
        revision: 9
      - key: UIS-RKG-001
        revision: 6
      - key: UXF-RKG-002
        revision: 4
      base_commit: 33d1eb8dc20d61a69aa2d2bd43bebfee6e69ecd4
      code_tree: working-tree-file-hashes-below
      pins:
        cpython: 3.12.14
  record: "# DIARY-TASK-RKG-021 — Conversation API and UI\n\n## Thực hiện\n\n- `POST/GET /api/v1/conversations`,\
    \ `GET /conversations/{id}/turns` và\n  `POST /conversations/{id}/turns` gọi service hội thoại đã\
    \ có. Delete giữ\n  `409 conversation_busy` khi còn turn `pending`.\n- Mutation và lượt hỏi thiếu\
    \ `X-RKG-Session` hoặc Origin/Host ngoài loopback\n  nhận `401` trước khi gọi provider. Câu quá dài\
    \ hoặc thiếu revision/request id\n  nhận `422` và không tạo turn. Provider lỗi là `502`, tắt là\n\
    \  `503 llm_disabled`, timeout là `504 llm_timeout`; focus đã commit không đổi.\n  Snapshot pin mất\
    \ trả `410 snapshot_unavailable` và không chuyển sang snapshot khác.\n- UI Ask tạo, mở, xóa (có xác\
    \ nhận), xem lịch sử, hỏi tiếp, chọn candidate theo\n  thứ tự, giữ draft khi conflict, mở citation\
    \ và báo provider tắt. Nội dung\n  repository/model được render dạng text.\n\n## Kiểm chứng trên cây\
    \ mã hiện tại\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `uv run pytest tests -q` | 132 passed, 4 skipped\
    \ |\n| `uv run ruff check src tests` | pass |\n| `npm test` trong `frontend` | 27 passed |\n| `npx\
    \ tsc -b` trong `frontend` | pass |\n\nSHA-256 của file đã kiểm chứng:\n\n| File | SHA-256 |\n| ---\
    \ | --- |\n| `src/rkg/api/__init__.py` | `0c054c3b4b550012faba34036d33088100cfaceb7287139e5cb118fac2952406`\
    \ |\n| `src/rkg/api/README.md` | `0a4926b5e2c408d690d9ec3090b6e5d964495ad44a56d14bf3bf6817a5a83b47`\
    \ |\n| `src/rkg/api/app.py` | `0fba0877ce2d327f5921ebc60f8af063b601d5831125cb318794f65031946565` |\n\
    | `src/rkg/api/conversations.py` | `2d46751d9bb3914a3303e7a23d7cae98d7cb31daf2f231e768184baf0393072f`\
    \ |\n| `src/rkg/api/errors.py` | `0e1751e2496b9767ea465ae9e29f9aa8bee586d0f8f9da88f3ecf654ae366cdd`\
    \ |\n| `src/rkg/conversations/__init__.py` | `0814a0a1b89ca81e9134f65392b339d8b487484b6f15a063435a3cfe7979747f`\
    \ |\n| `src/rkg/conversations/README.md` | `adf38c4220f53e0b60bf4af62d641fd8e262e49e93a8327a971b09a71ab0227f`\
    \ |\n| `src/rkg/conversations/service.py` | `ed6c453d2b0a2b78db599aa22462452808007ae56c8ef802e6d03a825321d24f`\
    \ |\n| `src/rkg/storage/conversations.py` | `b02ca35e804c4d32e3c164e5232277f27698b298cc80def62576b943d60814bf`\
    \ |\n| `src/rkg/storage/connection.py` | `d86c668089aae3230ef402bed5b873bf46fa86dc2e20d5fb3cebb5a23e8ca2fe`\
    \ |\n| `tests/integration/test_conversation_api.py` | `4c4fcfa81671c176b36342a22071da44e54140cc5a773b2e1e7a844b73f1b5bc`\
    \ |\n| `frontend/src/App.tsx` | `a78c7f6154622a4ef68e56b516e805b6529d01ad34d80d59c539e67dfdc386cf`\
    \ |\n| `frontend/src/pages/conversations/ConversationsPage.tsx` | `ad3d6fb493f4ffdb83ec2b3c589a2a5eb0113dedf21c825e6eade95e869da84b`\
    \ |\n| `frontend/src/pages/conversations/ConversationPage.tsx` | `97365f1ad07611f72cb307c95a429529d274e00b6f42d2334f7eca292df46db6`\
    \ |\n| `frontend/src/pages/conversations/ConversationPage.test.tsx` | `0fe1952aa505cc172af8ee9e6d7dee87c47cb509d211e664c72c7029fcad4fd1`\
    \ |\n| `frontend/src/client/mock/mockClient.ts` | `cf4f9584279cc5ee777ce6bcefc89343cb7fd8e8384fada24f97049e1955dc75`\
    \ |\n| `frontend/src/client/live/liveClient.ts` | `1bab3b729c104af9f579ee4ddf0b7393c75850af5a260327ba236c82f5a0a281`\
    \ |\n| `frontend/src/client/live/mapWire.ts` | `5345f3c6557cfdbda1e1dfa008d3612a12441c1d259d4a8afe71b7332318e404`\
    \ |\n| `frontend/src/types/api.ts` | `59643ec831a3041982e53bc98dee9060407b4f8bde490bd80af0953f48d9ce01`\
    \ |\n| `frontend/src/components/ui/ConfirmDialog.tsx` | `ea9f113e1643c8195a8e2af549bc1f53b6700a8bbde6a298b7ec3ec1eb0cd69b`\
    \ |\n| `frontend/src/i18n/en.ts` | `f534de6884cb7b6c152313ae21050e5faad4c530269296cae3e1b6598b02541a`\
    \ |\n| `frontend/src/i18n/vi.ts` | `7c91e3c19f307a43475ea8ff370cd92808c2332fc963591d90171a343916d6f7`\
    \ |\n| `frontend/src/index.css` | `e62169328968c8c792dded462a9eb7dd9baec0da83915257b10a0be587c675cc`\
    \ |\n| `.aide/lifecycle/tasks/TASK-RKG-021.md` | `633bbab5ad4205f4e40ab7c0d3be3653f015f25c1abc45c7108d6cf71843e66d`\
    \ |\n\n## Giới hạn\n\n- Cờ `history_truncated` / `retrieval_truncated` trả trên response của lượt\
    \ hỏi\n  và UI đang mở giữ chúng. Chúng không được lưu trên dòng Turn, nên tải lại trang\n  không\
    \ tự tính lại cờ đó. Cửa sổ lịch sử vẫn do service T-020 áp dụng.\n- `GET .../turns` trả `410` khi\
    \ pin không đọc được, nên mở mới không hiện\n  transcript. Pin không bị chuyển. Nếu trang đã có lịch\
    \ sử rồi submit sau đó\n  nhận `410`, transcript trên màn hình được giữ và composer bị khóa.\n- Một\
    \ lượt hỏi giữ khóa writer trong lúc gọi provider vì graph read và model\n  dùng chung một kết nối\
    \ Kùzu. `rkg serve` vẫn là một worker local.\n- AC-RKG-047 dùng fixture local được index thật rồi\
    \ citation trên snapshot đó\n  với MockProvider chọn edge đã có. Live OpenRouter không được gọi trong\
    \ lần\n  kiểm này; không có key thì serve trả `503 llm_disabled`."
---

# DIARY-TASK-RKG-021

## Thực hiện

- `POST/GET /api/v1/conversations`, `GET /conversations/{id}/turns` và
  `POST /conversations/{id}/turns` gọi service hội thoại đã có. Delete giữ
  `409 conversation_busy` khi còn turn `pending`.
- Mutation và lượt hỏi thiếu `X-RKG-Session` hoặc Origin/Host ngoài loopback
  nhận `401` trước khi gọi provider. Câu quá dài hoặc thiếu revision/request id
  nhận `422` và không tạo turn. Provider lỗi là `502`, tắt là
  `503 llm_disabled`, timeout là `504 llm_timeout`; focus đã commit không đổi.
  Snapshot pin mất trả `410 snapshot_unavailable` và không chuyển sang snapshot khác.
- UI Ask tạo, mở, xóa (có xác nhận), xem lịch sử, hỏi tiếp, chọn candidate theo
  thứ tự, giữ draft khi conflict, mở citation và báo provider tắt. Nội dung
  repository/model được render dạng text.

## Kiểm chứng trên cây mã hiện tại

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest tests -q` | 132 passed, 4 skipped |
| `uv run ruff check src tests` | pass |
| `npm test` trong `frontend` | 27 passed |
| `npx tsc -b` trong `frontend` | pass |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/api/__init__.py` | `0c054c3b4b550012faba34036d33088100cfaceb7287139e5cb118fac2952406` |
| `src/rkg/api/README.md` | `0a4926b5e2c408d690d9ec3090b6e5d964495ad44a56d14bf3bf6817a5a83b47` |
| `src/rkg/api/app.py` | `0fba0877ce2d327f5921ebc60f8af063b601d5831125cb318794f65031946565` |
| `src/rkg/api/conversations.py` | `2d46751d9bb3914a3303e7a23d7cae98d7cb31daf2f231e768184baf0393072f` |
| `src/rkg/api/errors.py` | `0e1751e2496b9767ea465ae9e29f9aa8bee586d0f8f9da88f3ecf654ae366cdd` |
| `src/rkg/conversations/__init__.py` | `0814a0a1b89ca81e9134f65392b339d8b487484b6f15a063435a3cfe7979747f` |
| `src/rkg/conversations/README.md` | `adf38c4220f53e0b60bf4af62d641fd8e262e49e93a8327a971b09a71ab0227f` |
| `src/rkg/conversations/service.py` | `ed6c453d2b0a2b78db599aa22462452808007ae56c8ef802e6d03a825321d24f` |
| `src/rkg/storage/conversations.py` | `b02ca35e804c4d32e3c164e5232277f27698b298cc80def62576b943d60814bf` |
| `src/rkg/storage/connection.py` | `d86c668089aae3230ef402bed5b873bf46fa86dc2e20d5fb3cebb5a23e8ca2fe` |
| `tests/integration/test_conversation_api.py` | `4c4fcfa81671c176b36342a22071da44e54140cc5a773b2e1e7a844b73f1b5bc` |
| `frontend/src/App.tsx` | `a78c7f6154622a4ef68e56b516e805b6529d01ad34d80d59c539e67dfdc386cf` |
| `frontend/src/pages/conversations/ConversationsPage.tsx` | `ad3d6fb493f4ffdb83ec2b3c589a2a5eb0113dedf21c825e6eade95e869da84b` |
| `frontend/src/pages/conversations/ConversationPage.tsx` | `97365f1ad07611f72cb307c95a429529d274e00b6f42d2334f7eca292df46db6` |
| `frontend/src/pages/conversations/ConversationPage.test.tsx` | `0fe1952aa505cc172af8ee9e6d7dee87c47cb509d211e664c72c7029fcad4fd1` |
| `frontend/src/client/mock/mockClient.ts` | `cf4f9584279cc5ee777ce6bcefc89343cb7fd8e8384fada24f97049e1955dc75` |
| `frontend/src/client/live/liveClient.ts` | `1bab3b729c104af9f579ee4ddf0b7393c75850af5a260327ba236c82f5a0a281` |
| `frontend/src/client/live/mapWire.ts` | `5345f3c6557cfdbda1e1dfa008d3612a12441c1d259d4a8afe71b7332318e404` |
| `frontend/src/types/api.ts` | `59643ec831a3041982e53bc98dee9060407b4f8bde490bd80af0953f48d9ce01` |
| `frontend/src/components/ui/ConfirmDialog.tsx` | `ea9f113e1643c8195a8e2af549bc1f53b6700a8bbde6a298b7ec3ec1eb0cd69b` |
| `frontend/src/i18n/en.ts` | `f534de6884cb7b6c152313ae21050e5faad4c530269296cae3e1b6598b02541a` |
| `frontend/src/i18n/vi.ts` | `7c91e3c19f307a43475ea8ff370cd92808c2332fc963591d90171a343916d6f7` |
| `frontend/src/index.css` | `e62169328968c8c792dded462a9eb7dd9baec0da83915257b10a0be587c675cc` |
| `.aide/lifecycle/tasks/TASK-RKG-021.md` | `633bbab5ad4205f4e40ab7c0d3be3653f015f25c1abc45c7108d6cf71843e66d` |

## Giới hạn

- Cờ `history_truncated` / `retrieval_truncated` trả trên response của lượt hỏi
  và UI đang mở giữ chúng. Chúng không được lưu trên dòng Turn, nên tải lại trang
  không tự tính lại cờ đó. Cửa sổ lịch sử vẫn do service T-020 áp dụng.
- `GET .../turns` trả `410` khi pin không đọc được, nên mở mới không hiện
  transcript. Pin không bị chuyển. Nếu trang đã có lịch sử rồi submit sau đó
  nhận `410`, transcript trên màn hình được giữ và composer bị khóa.
- Một lượt hỏi giữ khóa writer trong lúc gọi provider vì graph read và model
  dùng chung một kết nối Kùzu. `rkg serve` vẫn là một worker local.
- AC-RKG-047 dùng fixture local được index thật rồi citation trên snapshot đó
  với MockProvider chọn edge đã có. Live OpenRouter không được gọi trong lần
  kiểm này; không có key thì serve trả `503 llm_disabled`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Wire conversation API/history/turn state, stable errors và UI Ask/pending/citation; giữ non-streaming response và snapshot isolation.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
