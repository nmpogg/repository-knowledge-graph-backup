---
key: UIM-RKG-001-WALKTHROUGH
type: ui-mock-walkthrough
group: evidence
non_normative: true
derived_from: [UIM-RKG-001, GATE-RKG-UIUX]
captured_at: 2026-09-21
---

# GATE-RKG-UIUX walkthrough — UIM-RKG-001

**Method:** `frontend/` React app với `mockClient` — mở
`generated/ui-mocks/index.html` (build từ `npm run build:ui-mock`) hoặc
`cd frontend && npm run dev`. Dữ liệu seed: `frontend/src/mock/fixture.ts`.

## Primary flows (no coach)

| Flow | Result |
|---|---|
| Repositories → **Tạo repository** / mở dòng → detail → **Start indexing** → job monitor → **Open Explorer** | Một CTA primary rõ trên từng màn; trạng thái job (queued → … → succeeded / failed) hiển thị trên `JobScreen` |
| Explorer: search + preset → chọn node → drawer Evidence (copy `relative_path:line`) | Selection: outline + heading trong drawer; status có icon + text (`repo-status--*`) |
| Nav **Ask** (khi đã activate snapshot) → conversation → citation mở evidence | Explorer/Ask disabled trong nav khi chưa có `snapshotId`; composer disabled khi không có snapshot / LLM-off theo mock |

## Empty / loading / error / warnings

| Surface | Observed (mock client) |
|---|---|
| Repository list loading | `loading-row` + spinner; không để panel trống |
| Repository list empty / lỗi | Empty hint + CTA **Tạo repository**; `banner error` + Retry **Tìm lại** |
| Job | Progress track + stage messages; `succeeded_with_warnings` → banner warn + link report trên detail |
| Job failed | `banner error` + recovery (quay detail / retry index theo UXF) |
| Explorer subgraph | Spinner **Loading subgraph…**; search results `aria-live="polite"` |
| Ask | Pending answer row; limitations / citations; disabled nav + title khi thiếu snapshot |

## Accessibility

- `:focus-visible` ring trên control (`index.css`)
- Nav: `aria-current="page"`, disabled Explorer/Ask có `title` giải thích
- Live region: `session` announce (`aria-live` polite/assertive)
- Graph: `GraphCanvas` có `graph-list-fallback` (SR-only list) bên cạnh canvas
- Trạng thái repo/snapshot: màu + label text + icon (không chỉ màu)
- `prefers-reduced-motion`: rút animation/transition trong CSS

## Responsive

Kiểm tra layout tại **375 / 768 / 1024 / 1440** (DevTools):

| Breakpoint | Behavior |
|---|---|
| ≤1024px | Shell nav icon-only; Explorer rail/drawer stack (`explorer-rail` / `explorer-drawer` border-bottom, max-height) |
| ≤768px | Page padding tighter; repo cards stack; chat composer column; table ẩn cột phụ |
| Graph | Chỉ vùng graph/explorer canvas được phép scroll ngang khi cần |

## Token + contrast

CSS variables bind `TOK-RKG-001` (IBM Plex Sans, JetBrains Mono, semantic colors).
Core pair AA: `evidence/tests/TEST-RKG-WCAG-CONTRAST.md`. Interactive states:
verify trên build thật / browser follow-up.

## Decision

Mock là presentation-only (build của `frontend/`). **Ký UXF / SCR / UID** (không ký mock)
để đóng UI/UX Gate.
