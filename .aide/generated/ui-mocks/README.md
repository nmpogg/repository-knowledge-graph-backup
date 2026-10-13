---
key: UIM-RKG-001
type: ui-mock-package
group: derived
non_normative: true
hand_written: true
derived_from: [UXF-RKG-001, UXF-RKG-002, UXF-RKG-003, SCR-RKG-001, UID-RKG-001, TOK-RKG-001]
---

> Khi mock và UXF/SCR/UID bất đồng, **UXF/SCR/UID thắng**.
> Mock không được ký ở UI/UX Gate — chỉ là phương tiện trình bày.

# UI mock package — RKG MVP (React / Vite)

Gói này là **bản build tĩnh** của `frontend/` (React + Vite, `mockClient` + fixture).
Không dùng dashboard HTML/CSS/JS riêng.

## Mở UI

| Cách | Lệnh / đường dẫn |
|---|---|
| Static (gate walkthrough) | Mở `generated/ui-mocks/index.html` trong trình duyệt (cần `file://` hoặc static server; asset dùng `base: ./`) |
| Dev (interactive) | `cd frontend && npm run dev` |
| Tái tạo static | `cd frontend && npm run build:ui-mock` |

## Files

| File / thư mục | Purpose |
|---|---|
| `index.html` | Entry Vite build |
| `assets/` | Bundled JS/CSS |
| `vite.svg` | Favicon |
| `WALKTHROUGH.md` | GATE-RKG-UIUX walkthrough record |

## Token binding

Theme trong `frontend/src/index.css` map semantic tokens tới `TOK-RKG-001`
(`color.*`, `font.*`, `space.*`, `motion.*`). Font load: IBM Plex Sans / JetBrains Mono.

## Screens (SCR-RKG-001 decision set)

Repository catalog · Repository detail / job · Explorer + evidence drawer · Conversation (Ask).
Các SCR còn lại kế thừa shell và component system này.

## Source of truth

Implementation: `frontend/src/` — `App.tsx`, `layout/AppShell.tsx`, `screens/*`, `mock/*`.
