# Prompt tạo project test `rkg-fixture-laravel-orders`

## Vai trò và mục tiêu

Bạn là kỹ sư senior PHP/Laravel. Hãy tạo một project Laravel nhỏ, build/test được, dùng làm
corpus tĩnh cho adapter PHP/Laravel sau này. Project chỉ là fixture phân tích source: vài API
REST cơ bản trên domain đơn hàng. Không cần kiến trúc lớn, queue, event bus, auth thật hay
đa service.

**Chưa viết code adapter.** Không tạo file dưới `src/rkg/adapters/`, không sửa registry adapter,
không thêm test conformance, và không index graph.

## Đặt project ở đâu

Tạo toàn bộ project tại thư mục này, tính từ root repository RKG:

`repo-test/rkg-fixture-laravel-orders`

- Làm việc chỉ trong thư mục đó.
- Không tạo Git repository mới và không commit từ prompt này.
- Không đặt project ở root RKG, ngoài `repo-test/`, hay trong `tests/fixtures/`.
- Không commit `vendor/`, `node_modules/`, `.env`, cache, log hay IDE metadata.
- Commit được `composer.lock` khi có người commit sau; file đó nằm trong project.

## Tài liệu được sửa và tài liệu không đụng

Chỉ viết tài liệu của chính fixture:

- `repo-test/rkg-fixture-laravel-orders/README.md` — stack/version thật, lệnh chạy, bảng
  endpoint, inventory fact dự kiến, negative case.
- `repo-test/rkg-fixture-laravel-orders/.env.example` — chỉ giá trị giả.
- `repo-test/rkg-fixture-laravel-orders/.gitignore` — loại `vendor/`, `.env`, cache Laravel.

Không sửa:

- `.aide/` (requirement, registry `REG-ADAPTER-001`, task, evidence, ADR).
- `src/`, `tests/` của RKG.
- `README.md` ở root RKG.
- `repo-test/README.md` và các prompt `01`–`06`. Catalog prompt đã có dòng cho file này;
  agent tạo project không cập nhật catalog.

README của fixture mô tả fact dự kiến bằng ngôn ngữ thường (class, method, route, table).
Không hard-code ID RKG (`FR-RKG-*`, `AC-RKG-*`, node id).

## Stack bắt buộc

- PHP `8.3`.
- Laravel stable hiện tại (ưu tiên Laravel 11 hoặc 12; ghi đúng version đã cài trong README).
- Eloquent, route file `routes/api.php`, Form Request hoặc validation đơn giản.
- PHPUnit đi kèm Laravel. Dùng SQLite in-memory cho test.
- Composer. Không thêm frontend Vite app, không bắt buộc npm.
- Không Docker, không PostgreSQL, không Redis, không queue worker.

## Domain chức năng

Order API nhỏ:

| HTTP method | Path | Việc làm |
|---|---|---|
| `POST` | `/api/orders` | tạo đơn và các dòng hàng |
| `GET` | `/api/orders` | danh sách |
| `GET` | `/api/orders/{order}` | chi tiết một đơn |
| `PATCH` | `/api/orders/{order}` | đổi trạng thái |
| `GET` | `/api/health` | readiness, không đụng database |

Không authentication. Dữ liệu test dùng id/string giả, không PII thật.
Status chỉ gồm `pending`, `paid`, `cancelled`.

## Cấu trúc mong muốn

Giữ skeleton Laravel chuẩn và thêm các file sau. Có thể đổi tên nhỏ nếu convention Laravel
bắt buộc, nhưng giữ layer rõ và số file ít.

```text
repo-test/rkg-fixture-laravel-orders/
  app/Http/Controllers/OrderController.php
  app/Http/Controllers/HealthController.php
  app/Http/Requests/StoreOrderRequest.php
  app/Http/Requests/UpdateOrderStatusRequest.php
  app/Models/Order.php
  app/Models/OrderItem.php
  app/Services/OrderService.php
  app/Analysis/UnregisteredOrderController.php
  config/orders.php
  database/migrations/*_create_orders_table.php
  database/migrations/*_create_order_items_table.php
  routes/api.php
  tests/Feature/OrderApiTest.php
  tests/Feature/HealthTest.php
  tests/Unit/OrderServiceTest.php
  tests/fixtures/syntax-error.php.fixture
  README.md
  .env.example
```

`OrderController` nhận `OrderService` qua constructor và gọi service. `OrderService` dùng
`Order` / `OrderItem`. Không thêm repository interface, event, job, policy hay resource class
trừ khi một file đó làm API ngắn hơn mà không thêm layer mới.

## Pattern source cần có để adapter sau này đọc được

- Namespace và `use` rõ ràng.
- Một class, một interface không bắt buộc. Có `OrderService` là class thường.
- `Order` `hasMany` `OrderItem`; `OrderItem` `belongsTo` `Order`.
- Method instance trên controller và service; một static method nhỏ trên `Order` (ví dụ
  `allowedStatuses(): array`) để có callable tĩnh.
- Route khai báo tường minh trong `routes/api.php` bằng class và method, ví dụ
  `[OrderController::class, 'store']`. Không dùng invokable-only cho toàn bộ API và không
  dùng closure làm handler của năm endpoint trên.
- Path tĩnh. `{order}` là route parameter thường, implicit binding tới `Order`.
- `HealthController` là route thứ hai, cùng file route.
- `config/orders.php` đọc `env('ORDERS_CURRENCY', 'USD')`. Không đưa giá trị env vào fact
  mô tả trong README; README chỉ ghi key `ORDERS_CURRENCY`.
- `.env.example` có `ORDERS_CURRENCY=USD` và không có secret thật. Sentinel
  `RKG_TEST_SECRET_DO_NOT_PERSIST` chỉ xuất hiện trong comment của negative fixture, không
  nằm trong config được load.

## Persistence

Migration tạo:

- bảng `orders`: `id`, `status` (string), timestamps.
- bảng `order_items`: `id`, `order_id` foreign key, `sku` (string), `quantity` (integer),
  timestamps.

Schema mặc định của SQLite/Laravel, không khai báo schema tên riêng. README ghi table
`orders` và `order_items` là hai resource dự kiến. Không lưu giá trị cột hay payload vào
phần inventory.

`OrderService::create` ghi cả hai bảng. `list` và `show` đọc `orders` (show có items).
`updateStatus` ghi `orders`.

## Negative case, vẫn là source hợp lệ hoặc fixture tách riêng

- `app/Analysis/UnregisteredOrderController.php`: class có method giống `store` nhưng
  **không** được import trong `routes/api.php` và không được route nào trỏ tới. README nói
  rõ method này không phải endpoint.
- Trong `routes/api.php`, một dòng route bị comment, path lấy từ biến, ví dụ
  `$path = '/api/orders/' . $id`. Analyzer sau này không được đoán full path từ dòng comment
  đó. Ứng dụng chạy không load dòng này.
- `tests/fixtures/syntax-error.php.fixture` chứa PHP lỗi cú pháp. Đuôi `.fixture` để PHPUnit
  và Composer không parse file. README ghi một câu: khi dựng corpus syntax-error thì đổi
  thành `.php` trong bản copy, không đổi file gốc nếu làm vỡ tooling.

## README bắt buộc của fixture

`repo-test/rkg-fixture-laravel-orders/README.md` gồm:

- PHP và Laravel version thật (`php -v`, `php artisan --version`).
- Lệnh cài và test.
- Sơ đồ ngắn: HTTP → controller → `OrderService` → Eloquent.
- Bảng endpoint: method, full path, handler `Class::method`.
- Bảng class/method quan trọng.
- Quan hệ Eloquent dự kiến.
- Hai table `orders`, `order_items` và method nào đọc/ghi.
- Key cấu hình `ORDERS_CURRENCY` (không ghi giá trị như một fact).
- Negative case và fact không được tạo.

## Test bắt buộc

- Feature test hit đủ năm endpoint bằng HTTP test của Laravel, SQLite in-memory.
- `POST` trả 201 và tạo order cùng ít nhất một item.
- `GET` list và `GET` detail.
- `PATCH` đổi status hợp lệ; status lạ trả 422.
- `GET /api/health` trả 200.
- Unit test `OrderService` với model hoặc SQLite, không mock framework cả ứng dụng.
- `php artisan test` xanh.

## Tiêu chí nghiệm thu

Trong `repo-test/rkg-fixture-laravel-orders`, sau khi dependency đã cache:

```bash
composer install
php artisan test
```

Không cần Docker hay network ở bước test. Cây thư mục không có `src/rkg/adapters/` mới và
không có diff ngoài `repo-test/rkg-fixture-laravel-orders/`.

Khi xong, trả về danh sách file đã tạo, lệnh đã chạy, kết quả test, và version PHP/Laravel.
Hãy tạo project chạy được, không chỉ snippet.
