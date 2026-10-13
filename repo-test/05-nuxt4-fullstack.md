# Prompt tạo repository `rkg-fixture-nuxt4`

## Vai trò và mục tiêu

Bạn là kỹ sư senior Vue/Nuxt. Hãy tạo repository standalone `rkg-fixture-nuxt4`, một ứng
dụng order portal nhỏ dùng Nuxt 4. Repository phải chạy/test/build được và là golden fixture
để kiểm tra Vue Single File Component, TypeScript, file-based routing, auto-import và server
route extraction.

Không viết code RKG trong repo này. Làm việc chỉ trong repository hiện tại. Không commit
`node_modules`, `.nuxt`, `.output`, coverage, generated type output hoặc credential.

## Stack bắt buộc

- Node.js LTS.
- Nuxt 4 + Vue + TypeScript strict ở mức phù hợp với Nuxt.
- Vitest và Nuxt test utilities hoặc Vue Test Utils.
- ESLint module/config tương thích Nuxt.
- npm và `package-lock.json`.
- Chọn stable compatible versions và ghi phiên bản trong README.

Không thêm backend framework riêng. Dùng Nitro/server routes tích hợp của Nuxt.

## Domain chức năng

Order Customer Portal gồm:

- Trang `/`.
- Trang `/orders`.
- Trang động `/orders/[orderId]`.
- Nested account route `/account/profile`.
- Một client-only component hiển thị trạng thái kết nối.
- Một server-only component nhỏ nếu stable profile hỗ trợ rõ.
- Server API `GET /api/orders` và `GET /api/orders/[orderId]`.
- Server API `POST /api/orders/[orderId]/cancel`.
- Page gọi API qua `useFetch` hoặc `$fetch`.
- Runtime config tách public API base và server-only key placeholder.

Không cần database thật; server repository dùng in-memory fixture deterministic.

## Cấu trúc mong muốn

Tuân theo Nuxt 4 directory conventions, tối thiểu:

```text
app/
  app.vue
  pages/
    index.vue
    orders/
      index.vue
      [orderId].vue
    account/
      profile.vue
  components/
    OrderCard.vue
    OrderStatusBadge.vue
    ConnectionState.client.vue
  composables/
    useOrders.ts
  layouts/
    default.vue
  middleware/
    account.ts
server/
  api/
    orders/
      index.get.ts
      [orderId].get.ts
      [orderId]/cancel.post.ts
  repositories/
    orderRepository.ts
  services/
    orderService.ts
shared/
  types/
    order.ts
analysis-cases/
  positive/
  negative/
test/
```

Điều chỉnh đường dẫn theo convention chính xác của version Nuxt đã chọn, nhưng README phải ghi
rõ mapping giữa file và route.

## Vue SFC patterns bắt buộc

- Ít nhất một component dùng `<script setup lang="ts">`.
- Một component dùng standard `<script lang="ts">` với `defineComponent` để tạo hai kiểu parse.
- Template có component usage, props và emitted event.
- Scoped style nhỏ để parser phải hiểu SFC sections nhưng không cần graph CSS.
- Một file có type-only import và composable auto-import.
- Component `.client.vue`; nếu thêm `.server.vue`, phải bảo đảm build ổn định.
- README xác định một `.vue` file là một SourceUnit với structured SFC representation, không tách
  template/script/style thành source files giả.

## File-based routing

- Static page, index page, dynamic segment và nested directory.
- Route middleware cho account page.
- Có `definePageMeta` với metadata literal.
- Positive expected routes phải derive deterministic từ path.
- Negative case có custom/dynamic route extension hoặc runtime-generated path; analyzer không
  được đoán khi không đủ evidence.
- Phân biệt UI routes với Nitro HTTP endpoints trong expected inventory.

## Server routes

- Dùng file naming conventions `.get.ts` và `.post.ts`.
- Handler là named hoặc default exported callable có thể xác định source line.
- Route param được đọc từ event helper phù hợp.
- Handler gọi `orderService`, rồi repository.
- Không khởi động server hoặc đọc network khi import module.
- Có một dynamic handler registration trong negative case nằm ngoài scanned/runtime path.

## Auto-import và symbol resolution

- Một composable `useOrders` được Nuxt auto-import trong page.
- Một component auto-import và một component explicit import để so sánh.
- Server helper/service dùng explicit imports.
- Có hai symbols cùng simple name ở directories khác nhau trong negative case.
- README ghi rõ auto-import resolution phụ thuộc Nuxt conventions, không được biến thành guessed
  normal ES import khi rule chưa hỗ trợ.

## HTTP/configuration patterns

- Page gọi relative `/api/orders`.
- Server-side service có một absolute literal origin giả như
  `https://inventory.example.test` để tạo external dependency candidate.
- Có dynamic URL negative case.
- Dùng `runtimeConfig` với `inventoryApiBase` và `public.portalName`.
- `.env.example` chỉ chứa placeholder; sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` chỉ trong test.
- Expected graph chứa config key, không chứa config value, URL path/query/payload hoặc secret.

## Ignore/generated directories

README phải liệt kê `.nuxt/**`, `.output/**`, `node_modules/**`, `dist/**`, `coverage/**` là
generated/ignored paths. `.gitignore` phải bao phủ chúng. Không commit generated route/types.
Fixture này phải được dùng để xác nhận RKG áp dụng adapter ignore patterns trước file limits.

## Negative và syntax fixtures

- Dynamic UI route.
- Dynamic outbound URL.
- Ambiguous auto-import name.
- Runtime-computed server route nằm ngoài supported file convention.
- Shadowed `$fetch` hoặc `useFetch` local binding.
- Một `.vue.fixture` sai cú pháp không làm build thất bại; README hướng dẫn tạo syntax-error corpus.

## Expected inventory trong README

- Page/component/composable/server handler qualified names.
- Mapping file path → UI route.
- Mapping server file path → HTTP method/path/handler.
- Calls từ page/composable và server handler/service/repository.
- Configuration keys và external HTTP origin.
- Auto-import facts nào expected, facts nào còn detected-only.
- Negative/prohibited facts.

Không hard-code RKG IDs.

## Test bắt buộc

- Component rendering và props/event.
- Composable success/error với mocked `$fetch`.
- Page/route behavior tối thiểu.
- Nitro handlers gọi service đúng, không cần start server/network.
- Configuration/runtime config boundary.
- Server service/repository unit tests.

## Tiêu chí nghiệm thu

```bash
npm ci
npm run lint
npm test -- --run
npm run typecheck
npm run build
```

README phải có version, commands, file-route tables, expected graph inventory và intentional
negative cases. Khi hoàn tất, trả về danh sách file, lệnh đã chạy, kết quả và sai khác. Hãy thực
sự tạo repository hoàn chỉnh.

