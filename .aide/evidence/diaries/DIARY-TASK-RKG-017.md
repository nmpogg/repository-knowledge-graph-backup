---
key: DIARY-TASK-RKG-017
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-017
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - acb4a7fbc062f0ed3fcf05e5a52b5cf82c21ec5b
prior_evidence:
- evidence/context/CTX-TASK-RKG-017.yaml
- evidence/diaries/DIARY-TASK-RKG-017.md
- evidence/plans/PLAN-TASK-RKG-017.md
- evidence/tests/TEST-RKG-UI-MVP-MOCK-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-017
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-017
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-017
        revision: 10
      - key: UIS-RKG-001
        revision: 6
      - key: UID-RKG-001
        revision: 7
      - key: SCR-RKG-001
        revision: 7
      - key: API-RKG-CORE-v1
        revision: 9
      code_tree: frontend-mvp-mock-ui@09c7d74
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      node: 24.20.0
      npm: 11.19.0
  record: "# DIARY-TASK-RKG-017\n\n## Diễn giải\n\n- 2026-09-24 — Triển khai MVP UI (`frontend/`) với\
    \ **mock client** contract-shaped:\n  repository list/create/detail, index job monitor (poll + app\
    \ selection), Explorer\n  (search, presets, React Flow graph, list fallback, evidence/tech/deps/diags,\n\
    \  context export), shell + light/dark tokens.\n- Không sửa artifact thiết kế/FR/AC/API trong `.aide/design`\
    \ hay requirements;\n  presentation được tinh gọn (panel đóng/mở, toolbar gọn) so với blueprint dày.\n\
    - Ask/conversations chỉ placeholder (TASK-RKG-021). Live API thuộc TASK-RKG-024.\n- Destructive repository/snapshot\
    \ edit-delete guards đầy đủ thuộc TASK-RKG-025.\n\n## Đi chệch\n\n- Layout Explorer ưu tiên canvas:\
    \ panel trái/phải collapsible (`framer-motion`),\n  options depth/dir/max_nodes gom vào popover —\
    \ không bám cứng 240/360 cố định\n  lúc nào cũng mở.\n- Graph dùng `@xyflow/react`; layout radial\
    \ đơn giản (không dagre).\n- Fixture demo `Orders API` seed sẵn snapshot để người mới vào Explorer\
    \ ngay.\n\n## Đánh đổi\n\n- `RkgClient` mock in-memory; `VITE_RKG_CLIENT=live` reserved, vẫn trỏ mock\
    \ đến T-024.\n- AC M0 xác minh bằng Vitest mock + lint/build + walkthrough thủ công; chưa có\n  Playwright\
    \ E2E hay checklist viewport đầy đủ (AC-RKG-056 phần visual checklist\n  còn thiếu evidence riêng\
    \ — theme/token/reduced-motion CSS đã có trong UI).\n\n## Lệnh đã chạy và kết quả\n\n| Lệnh | Kết\
    \ quả |\n| --- | --- |\n| `cd frontend && npm run lint` | pass — oxlint (warnings only-export-components\
    \ / set-state-in-effect) |\n| `cd frontend && npm test` | pass — 5 tests (App landing + mock client)\
    \ |\n| `cd frontend && npm run build` | pass — `tsc -b` + Vite 8 production build |\n\n## M0 AC coverage\
    \ (mock UI)\n\n| AC | Phần M0 đã chứng minh trên mock |\n| --- | --- |\n| AC-RKG-011 | Search → select\
    \ → graph/list → evidence → export dialog/JSON |\n| AC-RKG-018 | Presets API→DB, Event, Config users,\
    \ Interface implementations |\n| AC-RKG-027 | Create local repo → index job stages → open Explorer;\
    \ failure path message giữ snapshot |\n| AC-RKG-043 | Job detecting + multiple app candidates; explicit\
    \ radio, tech non-blocking |\n| AC-RKG-054 | Path `missing` / `outside` → `422 invalid_input`, không\
    \ tạo repo |\n| AC-RKG-056 | Light/dark toggle, local fonts, `prefers-reduced-motion`; chưa checklist\
    \ 375–1440 riêng |\n| AC-RKG-057 | Tech support states + deps provenance filter |\n| AC-RKG-061 |\
    \ `useJobPolling` honor Retry-After cap 5s, stop terminal, cancel on unmount |\n| AC-RKG-066 | Create\
    \ + list/detail (paged shape); delete/conflict UI → T-025 |\n| AC-RKG-068 | Index publish mock snapshot;\
    \ job gắn `repository_id`; list snapshot newest-first |\n\n## DoD TASK-RKG-017\n\n- [x] Onboarding\
    \ create/select + job states trên mock\n- [x] Explorer + evidence/dependency/technology + context\
    \ export\n- [x] Contract-shaped fixtures / mock client\n- [x] Smoke lint/test/build trên revision\
    \ đã kiểm\n- [x] Evidence diary; task → `done`\n\n## Không làm / bàn giao tiếp\n\n- TASK-RKG-025:\
    \ edit/delete repository & snapshot, conflict/blocked confirms.\n- TASK-RKG-024: thay mock bằng live\
    \ API.\n- TASK-RKG-021: Ask/conversation UI.\n---"
---

# DIARY-TASK-RKG-017

## Diễn giải

- 2026-09-24 — Triển khai MVP UI (`frontend/`) với **mock client** contract-shaped:
  repository list/create/detail, index job monitor (poll + app selection), Explorer
  (search, presets, React Flow graph, list fallback, evidence/tech/deps/diags,
  context export), shell + light/dark tokens.
- Không sửa artifact thiết kế/FR/AC/API trong `.aide/design` hay requirements;
  presentation được tinh gọn (panel đóng/mở, toolbar gọn) so với blueprint dày.
- Ask/conversations chỉ placeholder (TASK-RKG-021). Live API thuộc TASK-RKG-024.
- Destructive repository/snapshot edit-delete guards đầy đủ thuộc TASK-RKG-025.

## Đi chệch

- Layout Explorer ưu tiên canvas: panel trái/phải collapsible (`framer-motion`),
  options depth/dir/max_nodes gom vào popover — không bám cứng 240/360 cố định
  lúc nào cũng mở.
- Graph dùng `@xyflow/react`; layout radial đơn giản (không dagre).
- Fixture demo `Orders API` seed sẵn snapshot để người mới vào Explorer ngay.

## Đánh đổi

- `RkgClient` mock in-memory; `VITE_RKG_CLIENT=live` reserved, vẫn trỏ mock đến T-024.
- AC M0 xác minh bằng Vitest mock + lint/build + walkthrough thủ công; chưa có
  Playwright E2E hay checklist viewport đầy đủ (AC-RKG-056 phần visual checklist
  còn thiếu evidence riêng — theme/token/reduced-motion CSS đã có trong UI).

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| --- | --- |
| `cd frontend && npm run lint` | pass — oxlint (warnings only-export-components / set-state-in-effect) |
| `cd frontend && npm test` | pass — 5 tests (App landing + mock client) |
| `cd frontend && npm run build` | pass — `tsc -b` + Vite 8 production build |

## M0 AC coverage (mock UI)

| AC | Phần M0 đã chứng minh trên mock |
| --- | --- |
| AC-RKG-011 | Search → select → graph/list → evidence → export dialog/JSON |
| AC-RKG-018 | Presets API→DB, Event, Config users, Interface implementations |
| AC-RKG-027 | Create local repo → index job stages → open Explorer; failure path message giữ snapshot |
| AC-RKG-043 | Job detecting + multiple app candidates; explicit radio, tech non-blocking |
| AC-RKG-054 | Path `missing` / `outside` → `422 invalid_input`, không tạo repo |
| AC-RKG-056 | Light/dark toggle, local fonts, `prefers-reduced-motion`; chưa checklist 375–1440 riêng |
| AC-RKG-057 | Tech support states + deps provenance filter |
| AC-RKG-061 | `useJobPolling` honor Retry-After cap 5s, stop terminal, cancel on unmount |
| AC-RKG-066 | Create + list/detail (paged shape); delete/conflict UI → T-025 |
| AC-RKG-068 | Index publish mock snapshot; job gắn `repository_id`; list snapshot newest-first |

## DoD TASK-RKG-017

- [x] Onboarding create/select + job states trên mock
- [x] Explorer + evidence/dependency/technology + context export
- [x] Contract-shaped fixtures / mock client
- [x] Smoke lint/test/build trên revision đã kiểm
- [x] Evidence diary; task → `done`

## Không làm / bàn giao tiếp

- TASK-RKG-025: edit/delete repository & snapshot, conflict/blocked confirms.
- TASK-RKG-024: thay mock bằng live API.
- TASK-RKG-021: Ask/conversation UI.
---

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Dựng onboarding/job/Explorer/evidence/context UI bằng typed mock client, design tokens và loading/empty/error/truncated states; chưa nhận là live backend.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
