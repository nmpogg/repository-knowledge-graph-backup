# Prompt tạo repository `rkg-fixture-spring-orders`

## Vai trò và mục tiêu

Bạn là kỹ sư senior Java/Spring. Hãy tạo một repository standalone tên
`rkg-fixture-spring-orders`: backend quản lý đơn hàng nhỏ, có REST API, dependency injection,
JPA và Kafka. Repository phải build/test được và là golden fixture để phát triển Java language
adapter cùng các Spring Web, Spring Data JPA và Spring Kafka deep adapter cho RKG.

Không viết code RKG trong repo này. Không yêu cầu Docker, PostgreSQL hoặc Kafka thật để chạy
unit test. Làm việc chỉ trong repository hiện tại. Không commit build output, IDE metadata hoặc
credential.

## Stack bắt buộc

- Java LTS phù hợp với Spring Boot stable đã chọn.
- Spring Boot.
- Spring Web MVC, không dùng WebFlux trong fixture đầu tiên.
- Spring Data JPA với Jakarta Persistence annotations.
- Spring Kafka.
- Bean Validation.
- JUnit 5, AssertJ và Mockito; dùng test slice khi phù hợp.
- Chọn Maven **hoặc** Gradle, ưu tiên Maven cho fixture đầu tiên; không tạo đồng thời cả hai.
- Commit wrapper và dependency lock/effective reproducibility artifact nếu ecosystem hỗ trợ.
- Ghi rõ version thực tế trong README.

## Domain chức năng

Order service cung cấp:

- `POST /api/orders` tạo đơn hàng.
- `GET /api/orders/{orderId}` đọc chi tiết.
- `GET /api/orders` tìm danh sách.
- `PATCH /api/orders/{orderId}/status` cập nhật trạng thái.
- Sau khi tạo/cập nhật, publish event vào topic `orders.events`.
- Consume topic `payments.events` để cập nhật trạng thái thanh toán.
- Persistence gồm `orders` và `order_items`, schema literal `commerce`.

Không cần authentication thật. Dữ liệu test dùng UUID/string giả và không chứa PII thật.

## Package và cấu trúc mong muốn

Dùng base package `com.example.rkgfixture.orders`:

```text
src/main/java/com/example/rkgfixture/orders/
  OrdersApplication.java
  api/
    OrderController.java
    OrderRequest.java
    OrderResponse.java
  application/
    OrderService.java
    DefaultOrderService.java
  domain/
    Order.java
    OrderItem.java
    OrderStatus.java
    OrderNotFoundException.java
  persistence/
    OrderEntity.java
    OrderItemEntity.java
    OrderJpaRepository.java
    JpaOrderRepository.java
  messaging/
    OrderEventPublisher.java
    KafkaOrderEventPublisher.java
    PaymentEventListener.java
  config/
    KafkaConfiguration.java
    OrderProperties.java
  analysiscases/
    positive/
    negative/
src/main/resources/
  application.yml
src/test/java/...
```

Có thể điều chỉnh package nhỏ nhưng giữ layer rõ ràng và không tạo kiến trúc quá lớn.

## Pattern Java language adapter bắt buộc

- Package declaration và imports rõ ràng.
- Class, interface, enum và record.
- Constructor, instance method, static method và overloaded method.
- Interface `OrderService` được `DefaultOrderService` implements explicit.
- Direct inheritance đơn giản cho một test type; không lạm dụng inheritance trong domain.
- Nested static type nhỏ để kiểm tra lexical containment.
- Direct import, wildcard import trong negative case, static import và fully qualified reference.
- Hai class có cùng simple name ở package khác nhau để kiểm tra ambiguous/simple-name resolution.
- Qualified method identity phải phân biệt overload bằng signature trong expected inventory.

## Spring Web patterns

- `@RestController` và class-level `@RequestMapping("/api/orders")`.
- Method-level `@PostMapping`, `@GetMapping`, `@PatchMapping`.
- Path variable, request body, validation và response status.
- Một endpoint có nhiều HTTP methods hoặc composed annotation nếu Spring version hỗ trợ rõ.
- Handler gọi service qua constructor injection.
- Có một controller/helper không được component scan hoặc không được đăng ký; method annotation
  trong đó không được coi là exposed endpoint.
- Có path lấy từ `static final String` resolve duy nhất.
- Có dynamic/property-placeholder path trong negative case; không đoán full path nếu contract
  chưa hỗ trợ resolution tĩnh.

## Dependency injection

- Ưu tiên constructor injection.
- Controller phụ thuộc interface service; implementation được component scan rõ ràng.
- Service phụ thuộc repository abstraction và event publisher.
- Có một ambiguous multi-implementation case cô lập trong `analysiscases.negative`, không được
  load vào application context bình thường; README mô tả expected diagnostic.
- Declared dependency phải là `depends_on`, không tự động biến thành call edge nếu không có call.

## JPA patterns

- `@Entity`, `@Table(name = "orders", schema = "commerce")` và entity `order_items`.
- `@Id`, relationship đơn giản và repository interface.
- Có `findById`, `save`, list query và một `@Query` tĩnh đơn giản.
- Application callable phải có luồng read/write rõ ràng tới đúng resource.
- Có entity cùng table name nhưng schema khác trong negative/identity case để kiểm tra namespace.
- Có dynamic/native query case và table name không literal trong test resource/commented fixture;
  analyzer không được tạo fact suy đoán.
- Không lưu column values hoặc SQL parameter/payload vào expected graph.

## Kafka patterns

- Topic constants `orders.events` và `payments.events`, gán đúng một lần.
- Publisher dùng `KafkaTemplate.send` với imported/static final topic.
- Consumer dùng `@KafkaListener(topics = ...)` trỏ tới literal hoặc constant tĩnh được hỗ trợ.
- Listener gọi application service rõ ràng.
- Có dynamic topic expression trong negative case, được cô lập khỏi runtime config.
- Payload/schema/Bootstrap server không được đưa vào graph fact.

## Configuration và security

- `@ConfigurationProperties(prefix = "orders")` cho các field không nhạy cảm.
- Dùng environment/property placeholders trong `application.yml` nhưng chỉ commit default giả.
- Có keys cho datasource URL, Kafka bootstrap và service option; expected graph chỉ chứa key,
  không chứa value.
- Sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` chỉ nằm trong test resource và danh sách negative.
- Không log connection strings, event payload hoặc exception chứa config thô.

## Negative/syntax fixtures

- Đặt intentional negative cases ở package không được component scan hoặc dưới test resources.
- Thêm `src/test/resources/analysis/syntax-error.java.fixture` chứa Java lỗi cú pháp để analyzer
  test riêng mà không làm Maven build thất bại.
- README giải thích cách đổi extension khi dựng syntax-error corpus.
- Mỗi negative fixture có comment chỉ ra fact nào không được tạo.

## Expected inventory trong README

Tạo bảng hoặc JSON-like listing bao gồm:

- SourceUnit/package/type/callable quan trọng.
- `implements` và `inherits_from` dự kiến.
- REST endpoint với method/full path/handler.
- Constructor DI dependencies.
- `DataResource` identity gồm kind/schema/table.
- `maps_to`, `reads`, `writes`.
- Kafka `MessageChannel`, `publishes`, `consumes`.
- Configuration keys.
- Negative cases và prohibited facts.

Không hard-code RKG IDs.

## Test bắt buộc

- Controller tests cho mọi endpoint bằng MockMvc.
- Service unit tests bằng mocks.
- JPA mapping/repository test bằng database in-memory phù hợp hoặc test metadata không cần Docker.
- Kafka publisher/listener tests bằng mocks, không cần broker.
- Application context smoke test.
- Test configuration binding.

## Tiêu chí nghiệm thu

Với Maven, tối thiểu:

```bash
./mvnw test
./mvnw verify
```

Nếu chọn Gradle, cung cấp command tương đương và wrapper. Build phải không cần Docker/network sau
khi dependencies đã được cache. README phải có stack/version, architecture, commands, endpoint
table, expected graph inventory và intentional negative cases.

Khi hoàn tất, trả về danh sách file, command đã chạy, kết quả test/build và mọi sai khác. Hãy
thực sự tạo repository hoàn chỉnh, không chỉ cung cấp snippet hoặc hướng dẫn.

