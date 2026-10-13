# RKG design artifact index

Thư mục này là handoff chuẩn tắc cho trải nghiệm web của Repository Knowledge Graph.
Thiết kế được dẫn xuất từ PRD, FR/NFR, API contract và các quyết định kiến trúc trong
`.aide/`; không suy ngược từ một frontend implementation.

## Nguồn và thứ tự ưu tiên

1. `product/prd/PRD-RKG.md` xác định mục tiêu, persona và phạm vi MVP.
2. `requirements/fr/FR-RKG-001..005.md` xác định hành vi và acceptance criteria.
3. `requirements/nfr/NFR-RKG-UX-001.md`, `NFR-RKG-SEC-001.md` và
   `NFR-RKG-REL-001.md` xác định accessibility, safe rendering và consistency.
4. `tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md` là nguồn cho endpoint,
   enum, limit và error semantics.
5. Các artifact trong thư mục này chuyển các ràng buộc trên thành flow, screen,
   visual language và UI behavior có thể triển khai.

`frontend/` hiện chỉ là **base toolchain** (TASK-RKG-001-r2) và không phải nguồn
thiết kế. Nội dung trong `.aide/generated/ui-mocks/` là ảnh chụp/prototype lịch
sử, không chuẩn tắc và không được dùng để ghi đè các artifact bên dưới.

## Bộ tài liệu

| Artifact | Vai trò | Dùng khi |
|---|---|---|
| `ux/UXF-RKG-001.md` | Onboarding → graph → evidence → export | Kiểm tra happy path và recovery của Explorer |
| `ux/UXF-RKG-002.md` | Grounded conversation | Thiết kế Ask, clarification, citation và retry |
| `ux/UXF-RKG-003.md` | Repository/snapshot lifecycle | Thiết kế CRUD, index, activate và delete guards |
| `ux/SCR-RKG-001.md` | Information architecture, route và screen blueprint | Dựng màn hình/responsive layout |
| `ui/UID-RKG-001.md` | Visual language, component rules và content style | Xây design system/component library |
| `ui/UIS-RKG-001.md` | Machine-readable state/action/API specification | Tạo client types, fixtures và acceptance tests |
| `ui/tokens/tokens.json` | Design tokens | Sinh theme variables; không tự thêm giá trị cục bộ |

## Quy tắc handoff

- UI dùng backend/API làm nguồn authoritative; state cục bộ chỉ phục vụ draft,
  selection và trạng thái trình bày.
- Label thân thiện có thể dịch enum nhưng không được tạo lifecycle enum mới.
- Mọi màn hình dữ liệu phải có loading, empty, ready, error và recovery phù hợp;
  destructive action phải có confirm/blocked state.
- Repository/snapshot identity phải luôn nhìn thấy tại Explorer và Conversation.
- Không render raw HTML, absolute host path, secret, raw source hoặc text chưa sanitize.
- Khi artifact chuẩn tắc đổi revision, UI/UX Gate trở lại `pending` cho đến khi có
  review và evidence mới trên đúng revision.

