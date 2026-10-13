# Prompt tạo repository `rkg-fixture-react-ts`

## Vai trò và mục tiêu

Bạn là kỹ sư senior TypeScript/React. Hãy tạo một repository standalone có tên
`rkg-fixture-react-ts`, là một ứng dụng quản trị đơn hàng nhỏ nhưng chạy được, có test
và được thiết kế có chủ đích để kiểm thử static repository analyzer.

Repository phải vừa là project React hợp lệ, vừa là golden fixture giàu pattern cho
việc phát triển language adapter JavaScript/TypeScript và framework adapter React Router.
Không viết parser hay code RKG trong repository này.

Làm việc chỉ trong thư mục repository hiện tại. Không đọc, sửa hoặc phụ thuộc vào source
của repository RKG. Không commit `node_modules`, `dist`, coverage output, credential hoặc
file generated không cần thiết.

## Stack bắt buộc

- Node.js LTS và TypeScript ở strict mode.
- Vite + React.
- React Router với route declaration tĩnh.
- Vitest và React Testing Library.
- ESLint phù hợp với TypeScript/React.
- Dùng npm và commit `package-lock.json`.
- Chọn các phiên bản stable tương thích với nhau, ghi rõ phiên bản thực tế trong README.

Không dùng framework meta/full-stack như Next.js hoặc Remix trong fixture này. Không dùng
code generation cho router. Mục tiêu là JSX/TSX và route registration tường minh.

## Domain chức năng

Ứng dụng là Order Operations Console, gồm:

- Trang tổng quan `/`.
- Danh sách đơn hàng `/orders`.
- Chi tiết đơn hàng `/orders/:orderId`.
- Trang chỉnh sửa `/orders/:orderId/edit`.
- Nhóm route quản trị `/admin/users` được bảo vệ bởi layout/auth guard.
- Route catch-all hiển thị not found.
- Service tải danh sách/chi tiết và cập nhật đơn hàng.
- Một component hiển thị trạng thái API và một error boundary đơn giản.

UI chỉ cần gọn, dễ hiểu; không cần design system lớn hoặc backend thật. Test dùng mock HTTP.

## Cấu trúc mong muốn

Có thể bổ sung file hợp lý nhưng giữ tối thiểu cấu trúc sau:

```text
src/
  main.tsx
  app/
    App.tsx
    router.tsx
    layouts/
      RootLayout.tsx
      AdminLayout.tsx
    routes/
      DashboardPage.tsx
      OrdersPage.tsx
      OrderDetailPage.tsx
      OrderEditPage.tsx
      AdminUsersPage.tsx
      NotFoundPage.tsx
  components/
    OrderStatusBadge.tsx
    LoadingState.tsx
  hooks/
    useOrders.ts
  services/
    httpClient.ts
    orderApi.ts
  domain/
    order.ts
  config/
    environment.ts
  analysis-cases/
    positive/
      importedConstants.ts
      aliasedCalls.ts
    negative/
      dynamicImport.ts
      dynamicUrl.ts
      ambiguousBinding.ts
      shadowedFetch.ts
  test/
    setup.ts
```

Thêm `index.html`, Vite config, TypeScript configs, ESLint config, `.gitignore`, README và
các test cần thiết.

## Pattern bắt buộc cho static analysis

### Imports và call graph dương tính

- Có direct named import, default import, namespace import và alias import.
- Có ít nhất một relative import đi qua `../` và một path alias `@/` được cấu hình nhất quán
  trong TypeScript và Vite.
- Một route component gọi hook; hook gọi `orderApi`; `orderApi` gọi `httpClient`.
- Có synchronous function, async function, arrow function và class method nhỏ.
- Mỗi target dương tính phải resolve duy nhất; tránh barrel cycle trong luồng chính.

### React Router

- Khai báo route tĩnh trong một module rõ ràng.
- Có nested route, layout route, index route, dynamic segment và catch-all.
- Có một route path lấy từ constant string được import đúng một target.
- Có một route dynamic/conditional trong `analysis-cases/negative` để analyzer phải đưa ra
  diagnostic thay vì đoán.
- Không dùng UI route như backend HTTP endpoint trong expected inventory; README phải phân
  biệt rõ navigation route và outbound HTTP dependency.

### HTTP dependency

- `httpClient` hỗ trợ base URL từ `import.meta.env.VITE_API_BASE_URL`.
- Có một lời gọi tới absolute literal origin, ví dụ `https://inventory.example.test`, để có
  candidate `ExternalDependency` rõ ràng.
- Có lời gọi relative `/api/orders` phục vụ app bình thường.
- Có dynamic URL trong negative case, ghép từ runtime input; README ghi rõ không được tạo
  origin fact suy đoán cho case này.
- Có local function tên `fetch` trong `shadowedFetch.ts` để kiểm tra analyzer không nhận nhầm
  thành global HTTP client.
- Không đưa query, payload, authorization header hoặc secret vào expected graph.

### Configuration

- Đọc các key `VITE_API_BASE_URL` và `VITE_ENABLE_ADMIN`.
- Thêm `.env.example` chỉ chứa placeholder an toàn.
- Có sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` trong một fixture/test và ghi rõ sentinel này
  không được xuất hiện trong graph, report hay log analyzer.
- Không commit `.env` thật.

### Dependency metadata

- `package.json` phải phân biệt dependencies và devDependencies.
- Lockfile phải nhất quán với manifest.
- Có ít nhất một package được khai báo và import thực tế, và một dev-only package không import
  từ production source.
- Không thêm dependency giả không dùng chỉ để làm nhiễu.

### Negative và diagnostic cases

Các file trong `analysis-cases/negative` phải có comment ngắn nêu expected behavior:

- Dynamic import target: không tạo internal import edge suy đoán.
- Dynamic HTTP URL: không tạo external origin suy đoán.
- Binding được gán lại hoặc có hai target: không tạo call edge suy đoán.
- Shadowed global/library name: không nhận nhầm technology.

Thêm một file `.invalid.ts.fixture` chứa TypeScript sai cú pháp. Không dùng extension `.ts`
để nó không làm hỏng build; README hướng dẫn khi tạo corpus syntax-error có thể copy nội dung
sang `syntax-error.ts` trong một branch/fixture riêng.

## Expected inventory trong README

Tạo bảng liệt kê tối thiểu:

- Source files quan trọng.
- Qualified names dự kiến cho components, hooks và services.
- Internal import/call edges chính.
- Route registration chain dự kiến.
- Configuration keys dự kiến.
- External HTTP origin dự kiến.
- Các negative case và fact tuyệt đối không được tạo.

Không hard-code entity ID hash của RKG; chỉ mô tả semantic fact theo tên/path/rule intent.

## Test bắt buộc

- Render router và xác nhận nested/dynamic routes hoạt động.
- Test hook/service với mock HTTP, không gọi network thật.
- Test environment parsing cho giá trị hợp lệ và thiếu key.
- Test ít nhất một component.
- Tất cả test deterministic và không phụ thuộc thời gian/network.

## Tiêu chí nghiệm thu

Các lệnh sau phải pass từ clean checkout:

```bash
npm ci
npm run lint
npm test -- --run
npm run build
npx tsc --noEmit
```

README phải có:

1. Mục tiêu fixture.
2. Stack và phiên bản.
3. Cách cài/test/build.
4. Sơ đồ module ngắn.
5. Expected static-analysis inventory.
6. Danh sách intentional negative cases.
7. Cam kết không có credential và không cần backend/network.

Khi hoàn tất, trả về danh sách file đã tạo, các lệnh đã chạy và kết quả; nêu rõ mọi sai khác
so với prompt. Không chỉ đưa hướng dẫn: hãy thực sự tạo đầy đủ repository.

