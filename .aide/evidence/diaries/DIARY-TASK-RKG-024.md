---
key: DIARY-TASK-RKG-024
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-024
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 9557874b42a5aeca69e6f36e860382a99481d342
prior_evidence:
- evidence/context/CTX-TASK-RKG-024.yaml
- evidence/diaries/DIARY-TASK-RKG-024.md
- evidence/plans/PLAN-TASK-RKG-024.md
- evidence/tests/TEST-RKG-UI-LIVE-API-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-024
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-024
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-024
        revision: 7
      - key: API-RKG-CORE-v1
        revision: 9
      - key: FR-RKG-001
        revision: 7
      - key: FR-RKG-002
        revision: 8
      - key: FR-RKG-003
        revision: 7
      - key: UID-RKG-001
        revision: 7
      code_tree: working-tree@4ed6103+task-024
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      node: 24.20.0
      npm: 11.19.0
      cpython: 3.12.14
  record: "# DIARY-TASK-RKG-024\n\n## Diễn giải\n\n- 2026-09-28 — Thay nhánh mock trong `getRkgClient`\
    \ bằng client `/api/v1` khi\n  `VITE_RKG_CLIENT=live`. Màn hình M0 không viết lại.\n- Mapper bù lệch\
    \ contract: trang phẳng của API, kiểu thực thể domain\n  (`Endpoint` → `endpoint`, `Callable` → `function`,\
    \ `ExternalDependency` →\n  `dependency`, …), cạnh `source_id`/`target_id`, evidence `file_path`,\n\
    \  stage job nội bộ (`scanning`/`parsing`/`extracting`/`publishing`), và job\n  `failed` với `app_selection_required`\
    \ thành stage `detecting` để màn job\n  hiện radio chọn app.\n- Session: UI gửi `VITE_RKG_SESSION`\
    \ như `X-RKG-Session`. Máy chủ không in\n  token. Dev server proxy `/api`; CORS chỉ phản chiếu origin\
    \ loopback.\n- Đường dẫn tuyệt đối trong evidence/message bị rút còn hai đoạn cuối. Mã lỗi\n  nguồn\
    \ (`source_not_found`, `source_outside_allowed_roots`, …) được giữ,\n  không gộp thành `invalid_input`.\n\
    \n## Đi chệch\n\n- Bộ lọc Explorer `interface` trả rỗng: schema domain không có entity\n  Interface.\
    \ Preset Interface implementations vẫn dùng cạnh `implements` /\n  `inherits_from` giữa các `Type`\
    \ (hiển thị `class`).\n- Provenance dependency trên wire là object/kind/origin. Client map sang\n\
    \  `declared` | `imported` | `usage` khi token đó có mặt; không bịa usage từ\n  một khai báo rỗng.\n\
    - AC-069 không có bước activate snapshot cũ: snapshot vừa publish đã active.\n- AC-056 không chạy\
    \ lại checklist viewport/contrast. Bố cục M0 giữ nguyên;\n  chỉ thêm màu node `dependency`.\n\n##\
    \ Đánh đổi\n\n- Poll job chọn app dùng `Retry-After` tối đa 5 giây vì backend để job đó ở\n  trạng\
    \ thái terminal `failed`, trong khi UI cần giữ màn `detecting`.\n\n## Lệnh đã chạy và kết quả\n\n\
    | Lệnh | Kết quả |\n| --- | --- |\n| `cd frontend && npm test` | pass — 24 Vitest, gồm round-trip\
    \ API thật |\n| `cd frontend && npm run lint` | pass — oxlint, warning có sẵn |\n| `cd frontend &&\
    \ npm run build` | pass — `tsc -b` + Vite |\n| `uv run pytest tests/integration/test_core_api.py::test_cors_reflects_loopback_origin_only`\
    \ | pass |\n\n## AC coverage\n\n| AC | Evidence |\n| --- | --- |\n| AC-RKG-011 | Round-trip: search\
    \ endpoint → subgraph → `POST /context` |\n| AC-RKG-018 | Preset M0 giữ direction/edge types; export\
    \ gửi `handled_by`/`calls` |\n| AC-RKG-027 | Đăng ký local, index tới stage thành công, mở graph |\n\
    | AC-RKG-043 | Hai app FastAPI → stage UI `detecting`, không auto-select |\n| AC-RKG-054 | Ngoài allowlist\
    \ và path không tồn tại trả 422, mã riêng |\n| AC-RKG-056 | Không chạy lại checklist hình ảnh; cấu\
    \ trúc M0 giữ nguyên |\n| AC-RKG-057 | Mapper provenance; fixture live không đủ bốn support state\
    \ |\n| AC-RKG-061 | `Retry-After` được đọc; hook poll M0 vẫn cap 5s và dừng khi terminal |\n| AC-RKG-066\
    \ | Create không tạo snapshot; list phân trang sau khi map envelope |\n| AC-RKG-067 | PATCH tăng revision;\
    \ revision cũ → `409 repository_conflict` |\n| AC-RKG-068 | Snapshot publish có `source_revision`\
    \ dạng `manifest:` |\n| AC-RKG-070 | Xóa snapshot active → `409 snapshot_active` |\n| AC-RKG-071 |\
    \ Xóa repository không tham chiếu → 204, đọc lại → 404 |\n| AC-RKG-072 | Snapshot của repository khác\
    \ → 404 |\n\n## DoD TASK-RKG-024\n\n- [x] Live client thay mock, giữ contract `RkgClient`\n- [x] Map\
    \ kiểu thực thể domain sang nhãn UI\n- [x] Round-trip onboarding/job/explorer/repository/snapshot\
    \ trên API thật\n- [x] Evidence diary + TEST-RKG-UI-LIVE-API-001\n- [x] Task → `done`\n\n## Không\
    \ làm / bàn giao tiếp\n\n- TASK-RKG-021: màn hội thoại vẫn là placeholder.\n- Activate một snapshot\
    \ không phải active (AC-069) khi đã có hai snapshot.\n---"
---

# DIARY-TASK-RKG-024

## Diễn giải

- 2026-09-28 — Thay nhánh mock trong `getRkgClient` bằng client `/api/v1` khi
  `VITE_RKG_CLIENT=live`. Màn hình M0 không viết lại.
- Mapper bù lệch contract: trang phẳng của API, kiểu thực thể domain
  (`Endpoint` → `endpoint`, `Callable` → `function`, `ExternalDependency` →
  `dependency`, …), cạnh `source_id`/`target_id`, evidence `file_path`,
  stage job nội bộ (`scanning`/`parsing`/`extracting`/`publishing`), và job
  `failed` với `app_selection_required` thành stage `detecting` để màn job
  hiện radio chọn app.
- Session: UI gửi `VITE_RKG_SESSION` như `X-RKG-Session`. Máy chủ không in
  token. Dev server proxy `/api`; CORS chỉ phản chiếu origin loopback.
- Đường dẫn tuyệt đối trong evidence/message bị rút còn hai đoạn cuối. Mã lỗi
  nguồn (`source_not_found`, `source_outside_allowed_roots`, …) được giữ,
  không gộp thành `invalid_input`.

## Đi chệch

- Bộ lọc Explorer `interface` trả rỗng: schema domain không có entity
  Interface. Preset Interface implementations vẫn dùng cạnh `implements` /
  `inherits_from` giữa các `Type` (hiển thị `class`).
- Provenance dependency trên wire là object/kind/origin. Client map sang
  `declared` | `imported` | `usage` khi token đó có mặt; không bịa usage từ
  một khai báo rỗng.
- AC-069 không có bước activate snapshot cũ: snapshot vừa publish đã active.
- AC-056 không chạy lại checklist viewport/contrast. Bố cục M0 giữ nguyên;
  chỉ thêm màu node `dependency`.

## Đánh đổi

- Poll job chọn app dùng `Retry-After` tối đa 5 giây vì backend để job đó ở
  trạng thái terminal `failed`, trong khi UI cần giữ màn `detecting`.

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| --- | --- |
| `cd frontend && npm test` | pass — 24 Vitest, gồm round-trip API thật |
| `cd frontend && npm run lint` | pass — oxlint, warning có sẵn |
| `cd frontend && npm run build` | pass — `tsc -b` + Vite |
| `uv run pytest tests/integration/test_core_api.py::test_cors_reflects_loopback_origin_only` | pass |

## AC coverage

| AC | Evidence |
| --- | --- |
| AC-RKG-011 | Round-trip: search endpoint → subgraph → `POST /context` |
| AC-RKG-018 | Preset M0 giữ direction/edge types; export gửi `handled_by`/`calls` |
| AC-RKG-027 | Đăng ký local, index tới stage thành công, mở graph |
| AC-RKG-043 | Hai app FastAPI → stage UI `detecting`, không auto-select |
| AC-RKG-054 | Ngoài allowlist và path không tồn tại trả 422, mã riêng |
| AC-RKG-056 | Không chạy lại checklist hình ảnh; cấu trúc M0 giữ nguyên |
| AC-RKG-057 | Mapper provenance; fixture live không đủ bốn support state |
| AC-RKG-061 | `Retry-After` được đọc; hook poll M0 vẫn cap 5s và dừng khi terminal |
| AC-RKG-066 | Create không tạo snapshot; list phân trang sau khi map envelope |
| AC-RKG-067 | PATCH tăng revision; revision cũ → `409 repository_conflict` |
| AC-RKG-068 | Snapshot publish có `source_revision` dạng `manifest:` |
| AC-RKG-070 | Xóa snapshot active → `409 snapshot_active` |
| AC-RKG-071 | Xóa repository không tham chiếu → 204, đọc lại → 404 |
| AC-RKG-072 | Snapshot của repository khác → 404 |

## DoD TASK-RKG-024

- [x] Live client thay mock, giữ contract `RkgClient`
- [x] Map kiểu thực thể domain sang nhãn UI
- [x] Round-trip onboarding/job/explorer/repository/snapshot trên API thật
- [x] Evidence diary + TEST-RKG-UI-LIVE-API-001
- [x] Task → `done`

## Không làm / bàn giao tiếp

- TASK-RKG-021: màn hội thoại vẫn là placeholder.
- Activate một snapshot không phải active (AC-069) khi đã có hai snapshot.
---

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Nối typed client đến API thật, map wire DTO, session/errors/polling và snapshot ownership; bảo đảm live/mock không lệch contract.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
