---
uid:
key: OQ-RKG-007
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 3
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations:
  part_of: [CHG-RKG-2026-001]
  blocks: []
classification: internal
ai_assisted: true
---
# Entity type for React Router UI navigation routes

## Câu hỏi

Canonical graph type nào mang path đăng ký React Router (ví dụ `/orders`,
`/orders/:orderId`, `*`) khi fixture và README khẳng định đây là **browser UI
navigation route**, không phải backend HTTP endpoint?

## Quyết định (resolved)

**Phương án 1** — tái dùng `Endpoint` với:

- `framework_kind=react-router` (hoặc framework router tương đương)
- attributes bắt buộc: `kind=navigation`, `path` / `route_path`
- **không** có HTTP `method`
- **không** emit repository `exposes` (không phải Exposed API HTTP)

UI route ≠ backend HTTP Endpoint về semantics sản phẩm; cùng logical type
`Endpoint` để flow policy CMP (root Endpoint → outgoing `handled_by` / `calls`)
áp dụng, với nhánh FE tách biệt theo `kind=navigation`.

## Lý do

- Tránh schema entity type mới (versioning riêng) khi CMP/FR đã mô tả flow gốc
  Endpoint/Callable.
- Phân biệt rõ với FastAPI/Flask qua attributes + không `exposes`.
- Explorer List/preset/copy đọc `kind=navigation` để gắn nhãn “UI route”,
  preset “UI → API”, không ép FastAPI-style method+path.

## Hệ quả

- TBL-RKG-GRAPH: Endpoint mô tả cả HTTP API và UI navigation (attribute-gated).
- REG-ADAPTER-001 / `rkg.react-router`: đã khớp quyết định này.
- REG-ADAPTER-001 / `rkg.nuxt`: khớp quyết định với `framework_kind=nuxt` (và
  `kind=navigation` trên page routes).
- TASK-RKG-042 conformance: assert `kind=navigation` + path inventory; không
  yêu cầu HTTP method.
- TASK-RKG-043 conformance: assert `kind=navigation` + path inventory cho Nuxt
  pages; không yêu cầu HTTP method trên navigation Endpoints. Nitro
  `server/api` vẫn là HTTP Endpoint (method+path), tách biệt navigation pages.
- Flow traversal: root navigation được phép mở rộng `depends_on` (config /
  external) mà không đổi mặc định root HTTP Endpoint.

## Phương án không chọn

2. Entity type mới — hoãn; chỉ mở lại nếu CMP/API cần type riêng.
3. Chỉ attribute trên SourceUnit/Callable — thiếu catalog entrypoint List ổn định.
