# Prompt tạo repository `rkg-fixture-dotnet-orders`

## Vai trò và mục tiêu

Bạn là kỹ sư senior C#/.NET. Hãy tạo một repository standalone tên
`rkg-fixture-dotnet-orders`: một REST API quản lý đơn hàng nhỏ, chạy được và có test,
để demo bổ sung **ngôn ngữ mới** cho Repository Knowledge Graph (RKG).

Fixture phải thể hiện ba bước mở rộng riêng: C# language adapter → ASP.NET Core
framework adapter → EF Core data-access adapter. Expected inventory là mục tiêu cho
adapter tương lai, không phải tuyên bố RKG hiện đã hỗ trợ C#.

Không viết parser, adapter hoặc code RKG trong fixture. Làm việc chỉ trong repository
đích; không đọc, sửa hoặc phụ thuộc source RKG. Fixture và prompt này không thay thế
nguồn yêu cầu chuẩn tắc trong `.aide/` của RKG.

## Stack và build

- .NET 10, C# 14, nullable reference types và implicit usings.
- ASP.NET Core controller-based Web API; không dùng Minimal API cho luồng chính.
- EF Core với SQLite in-memory; không cần database ngoài hoặc Docker.
- xUnit, ASP.NET Core `WebApplicationFactory` và fake HTTP transport.
- `global.json`, `Directory.Build.props`, `Orders.slnx` và NuGet source tường minh.
- Pin phiên bản dependency, tạo `packages.lock.json` cho cả app và test project;
  script kiểm chứng phải restore bằng `--locked-mode`.
- Build Release với warnings treated as errors.
- `.gitignore` bỏ `bin`, `obj`, `TestResults`, database file và IDE output.
- `.gitattributes` giữ line ending LF để source hash nhất quán giữa các máy.

Ghi phiên bản SDK/framework/package thực tế và lệnh đã kiểm chứng trong README.
Không tự bịa lockfile hoặc báo build/test pass nếu chưa thực thi.

## Domain và cấu trúc

Luồng chính:

```text
OrdersController -> OrderService -> IOrderRepository
                                       ^ implements
                                 EfOrderRepository -> OrdersDbContext
                                                         | orders
                                                         | order_items
```

Cấu trúc tối thiểu:

```text
src/Orders.Api/
  Program.cs
  Bootstrap/ServiceRegistration.cs
  Controllers/OrdersController.cs
  Contracts/
  Application/OrderService.cs
  Application/IOrderRepository.cs
  Domain/Order.cs
  Domain/OrderItem.cs
  Domain/OrderStatus.cs
  Persistence/OrdersDbContext.cs
  Persistence/EfOrderRepository.cs
  Integrations/ShippingClient.cs
  AnalysisCases/Positive/
  AnalysisCases/Negative/
tests/Orders.Api.Tests/
analysis-cases/negative/
expected/
scripts/verify.sh
scripts/verify.ps1
scripts/validate-inventory.py
README.md
```

Giữ fixture nhỏ, khoảng 30–50 file tổng cộng, không nhân bản source để tăng số lượng.
Application startup phải tường minh; mặc định bind `127.0.0.1`, không tự gọi dịch vụ ngoài.

## REST endpoints

| Method | ASP.NET route template | Handler |
|---|---|---|
| POST | `/api/orders` | `OrdersController.Create` |
| GET | `/api/orders/{id:guid}` | `OrdersController.Get` |
| GET | `/api/orders` | `OrdersController.List` |
| PATCH | `/api/orders/{id:guid}/status` | `OrdersController.UpdateStatus` |
| DELETE | `/api/orders/{id:guid}` | `OrdersController.Delete` |
| GET | `/api/orders/readiness` | `OrdersController.Readiness` |

- Ghép class-level `[Route]` với method-level HTTP attributes.
- POST trả 201 kèm Location; không tìm thấy đơn trả 404; DELETE thành công trả 204.
- Validate customer reference, SKU, danh sách item không rỗng, quantity 1–100 và enum status.
- Với request record, đặt validation metadata đúng trên constructor parameters để
  ASP.NET Core model validation hoạt động.
- Expected canonical path có thể chuẩn hóa `{id:guid}` thành `{id}`, nhưng phải giữ
  constraint `guid` trong metadata. Endpoint identity phải bao gồm HTTP method.

## Pattern dương tính cho static analysis

- Namespace, class, interface, enum, record, constructor, static method và async method.
- Hai overload `Order.Create(string)` và `Order.Create(string, IEnumerable<OrderItem>)`.
- Một `using` alias trỏ tới `Order`, gọi overload một tham số với target duy nhất.
- `EfOrderRepository implements IOrderRepository`.
- Constructor injection và registration
  `AddScoped<IOrderRepository, EfOrderRepository>()` tường minh.
- Call chain controller → service → repository interface; phân biệt dependency
  khai báo với method call có call site thật.
- `ToTable("orders")` và `ToTable("order_items")` tường minh; resource identity có
  application/DbContext context, không chỉ tên bảng. Không giả lập schema SQLite.
- Repository đọc đơn kèm items bằng `Include`, thêm entity, cập nhật và xóa entity.
- Một `ShippingClient` gọi literal URL `https://shipping.example.invalid/health`;
  không nối client này vào CRUD flow. Test dùng fake transport, không gọi network.

Không đổi call qua interface thành concrete method call nếu chưa có rule resolve
DI được kiểm chứng. Item writes qua graph-add/cascade-delete phải là optional facts
cho đến khi adapter có rule EF tương ứng; `SaveChangesAsync` không chứng minh ghi
mọi bảng được map trong DbContext.

## Case âm tính và diagnostic

- Ba type tên `OrderService` ở namespace application, sales và audit: không merge.
- Hai overload factory: không merge identity hoặc chọn sai overload.
- `IPaymentGateway` có hai implementation không đăng ký DI; lời gọi qua parameter
  interface không được chọn một implementation cụ thể.
- HTTP client nhận runtime URI: không đoán host, path hoặc endpoint target.
- Type có `[NonController]` và HTTP attribute: không tạo endpoint giả.
- File sai cú pháp dùng extension `.cs.fixture`, nằm ngoài build. README hướng dẫn
  đổi extension trên bản sao riêng để kiểm thử parser recovery.
- Một file extension chưa hỗ trợ, không biến thành C# SourceUnit.
- Sentinel giả `RKG_TEST_SECRET_DO_NOT_PERSIST` trong inert fixture; không xuất hiện
  trong graph, report hoặc log analyzer. Không dùng credential thật.

Case âm không làm hỏng native build và không phát sinh I/O ngoài khi chạy test mặc định.

## Expected inventory và câu hỏi demo

Tạo các file dễ đọc bằng người:

```text
expected/
  README.md
  applications.json
  entities.json
  edges.json
  diagnostics.json
  questions.json
  source-manifest.json
  prohibited-values.txt
```

- Dùng semantic keys, namespace-qualified names và method signatures; không dùng
  hash ID nội bộ của RKG.
- Phân stage `language`, `framework`, `data_access`; baseline chưa hỗ trợ không có
  kỳ vọng positive C# facts. Tách required, optional và prohibited facts.
- Mỗi fact có evidence path tương đối, line/marker ổn định và hash để phát hiện drift.
- Pin SHA-256 source, inert negative files, build manifests và package locks.
- Validator chỉ đọc source; kiểm tra references, evidence pins, endpoint identity
  và dependency locks. Không import/chạy C# hoặc dùng LLM để xác nhận graph facts.
- Không lưu raw source body, absolute host path, payload, config value hoặc credential
  trong expected graph hay evidence.
- Thêm khoảng 10 câu hỏi demo với đáp án về nghĩa, evidence và forbidden claims:
  luồng tạo đơn, mapping bảng, reads/writes, DI registration, overload, namespace
  collision, HTTP dependency, ambiguous dispatch và endpoint không tồn tại.
- Không tự thêm fixture vào parent chatbot golden set hoặc thay đổi mẫu số nghiệm thu.

## Test và tiêu chí nghiệm thu

Native tests phải kiểm tra CRUD roundtrip, Location header, status codes, validation,
literal readiness route, NonController exclusion, table mapping và item cascade
deletion. Test alias/overload/namespace cases và cả literal/runtime HTTP URL qua fake
transport. Dữ liệu test độc lập, không phụ thuộc thời gian hoặc dịch vụ thật.

Hai script verify cho shell và PowerShell phải fail khi bất kỳ bước nào lỗi:

```sh
python3 scripts/validate-inventory.py
dotnet restore Orders.slnx --locked-mode
dotnet build Orders.slnx --no-restore --configuration Release
dotnet test Orders.slnx --no-build --no-restore --configuration Release
```

Restore lần đầu cần NuGet; sau khi cache đủ dependencies, test không cần dịch vụ ngoài.
VSTest có thể cần socket local riêng dù HTTP TestServer chạy in-process.

README phải có hướng dẫn chạy độc lập và demo trước/sau theo từng adapter stage.
Nêu rõ khi index, RKG chỉ đọc source, không restore/build/test hoặc thực thi fixture.
Scanner phải ignore `**/bin/**`, `**/obj/**`, `**/TestResults/**`; test code có scope
riêng, không trộn vào expected inventory của application.

Khi hoàn tất, trả về cây thư mục, phiên bản thực tế, lệnh và kết quả verification,
expected inventory đã tạo và mọi giới hạn chưa kiểm chứng. Không chỉ mô tả cách làm:
hãy tạo fixture đầy đủ và xác minh nó.
