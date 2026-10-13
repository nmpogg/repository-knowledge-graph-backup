# Prompt tạo repository `rkg-fixture-go-event-worker`

## Vai trò và mục tiêu

Bạn là kỹ sư senior Go chuyên event-driven systems. Hãy tạo repository standalone
`rkg-fixture-go-event-worker`, một background worker xử lý order events bằng Kafka và lưu
projection vào PostgreSQL. Repository phải build/test được và là golden fixture để phát triển
Go language adapter, messaging adapter và data-access adapter cho RKG.

Không viết parser/RKG adapter trong repo này. Không chạy Kafka/PostgreSQL thật trong unit test.
Không thực thi network khi package được import. Chỉ làm việc trong repository hiện tại và không
commit binary, coverage output, vendor directory hoặc credential.

## Stack bắt buộc

- Một phiên bản Go stable được ghi trong `go.mod` và README.
- Kafka client: chọn một thư viện phổ biến, ưu tiên API có producer/consumer group tường minh.
- PostgreSQL: ưu tiên `pgx` với SQL tĩnh để pattern reads/writes dễ quan sát.
- Structured logging nhưng không log payload/config value nhạy cảm.
- Unit test dùng standard `testing`; có thể thêm assertion/mock library nhỏ nếu thật sự cần.
- `go.mod` và `go.sum` phải được commit và tidy.

## Domain chức năng

Worker thực hiện:

- Consume topic `orders.events`.
- Parse một event envelope tối thiểu.
- Gọi application service cập nhật order projection.
- Read/write bảng `commerce.order_projection`.
- Publish topic `orders.projection.updated` sau khi commit thành công.
- Chạy scheduled cleanup cho projection cũ.
- Có graceful shutdown thông qua `context.Context` và signal ở command entrypoint.

Không cần HTTP server trong fixture này.

## Cấu trúc mong muốn

```text
cmd/order-worker/
  main.go
internal/
  app/
    processor.go
    cleanup.go
  domain/
    order.go
    event.go
  messaging/
    topics.go
    consumer.go
    producer.go
    kafka_consumer.go
    kafka_producer.go
  storage/
    repository.go
    postgres_repository.go
    queries.go
  config/
    config.go
  analysiscases/
    positive/
      imported_topic.go
      interface_binding.go
    negative/
      dynamic_topic.go
      ambiguous_receiver.go
      shadowed_package.go
      package_level_publish.go
testdata/
  syntax-error.go.fixture
```

Giữ package nhỏ và idiomatic. Không tạo `pkg/` nếu không có public package thật.

## Pattern Go language adapter bắt buộc

- Nhiều package dưới `internal/` và một `main` package.
- Struct, named type, interface, function, method với pointer receiver và value receiver.
- Embedded struct hoặc embedded interface nhỏ.
- Import chuẩn, import alias và dot import chỉ trong negative fixture nếu cần.
- Function call, method call qua concrete receiver và qua interface.
- Constructor convention `NewXxx` trả về pointer.
- Một generic helper nhỏ để kiểm tra type parameter parsing, không làm business logic khó đọc.
- Hai package có symbol cùng simple name để kiểm tra qualified resolution.
- Không coi package directory là Namespace graph node; README chỉ mô tả package metadata.

## Interface semantics

Go implements interface ngầm. Trong expected inventory:

- Liệt kê concrete types thỏa `OrderRepository`, `EventConsumer`, `EventPublisher`.
- Đánh dấu đây là structural/implicit satisfaction, không yêu cầu RKG phát `implements` nếu
  canonical contract vẫn chỉ chấp nhận explicit declaration.
- Analyzer không được tạo implements edge chỉ vì trùng tên method; cần toàn bộ method set và
  rule profile rõ ràng nếu tính năng này được thêm sau.

Điểm này phải được giải thích rõ trong README để fixture làm lộ quyết định schema/profile thay vì
ép adapter suy đoán.

## Messaging patterns

- Constants `OrdersTopic = "orders.events"` và
  `ProjectionUpdatedTopic = "orders.projection.updated"`.
- Positive case dùng literal ở một nơi và imported constant ở nơi khác.
- Consumer group handler gọi processor trong một method có source location rõ.
- Producer publish sau processing thành công.
- Dynamic topic từ runtime input nằm trong negative case và không được tạo `MessageChannel`.
- Một local type/package identifier cố ý giống tên Kafka client để kiểm tra shadowing.
- Call ở package initialization hoặc ngoài callable không được gán sai cho một handler.
- Không đưa brokers, payload, key hoặc headers vào graph expectations.

## PostgreSQL patterns

- Dùng SQL constants tĩnh cho một SELECT, một INSERT/UPSERT và một DELETE cleanup.
- Repository methods: `FindByID`, `Upsert`, `DeleteOlderThan`.
- Table identity dự kiến là kind `table`, namespace/schema `commerce`, name
  `order_projection`.
- Có query dynamic/constructed trong negative case; không đoán target nếu rule chưa hỗ trợ.
- Không lưu SQL parameter values hoặc row data trong graph.
- Tách interface khỏi pgx implementation để call graph rõ ràng.

## Configuration và security

- Đọc keys `KAFKA_BROKERS`, `KAFKA_GROUP_ID`, `DATABASE_URL`, `CLEANUP_INTERVAL`.
- Parsing có validation và trả error, không panic trong library package.
- `.env.example` chỉ chứa placeholder an toàn dù Go app không tự load `.env`.
- Sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` nằm trong testdata/test và prohibited inventory.
- Error/log không in brokers, database URL hoặc raw event.

## Side-effect và entrypoint constraints

- Chỉ `cmd/order-worker/main.go` ghép dependency và khởi động process.
- Import package không mở connection, spawn goroutine hoặc đọc network.
- Constructors chỉ tạo object; connection/start phải explicit.
- Tests gọi processor/service trực tiếp với fakes.
- Graceful shutdown phải test được qua context cancellation.

## Negative và syntax cases

- Dynamic topic.
- Receiver/interface binding mơ hồ.
- Shadowed import/package name.
- Package-level invocation không thuộc callable.
- `testdata/syntax-error.go.fixture` chứa lỗi parse nhưng không làm `go test` thất bại.
- Mỗi case có comment và được mô tả trong README.

## Expected inventory trong README

Liệt kê:

- Source packages/files và important qualified names.
- Struct/interface/functions/methods chính.
- Internal call edges processor → repository/publisher.
- Topic channels và publish/consume edges.
- Table resource và read/write edges.
- Configuration keys.
- Explicit versus implicit interface semantics.
- Negative cases và prohibited facts.

Không hard-code RKG entity IDs.

## Test bắt buộc

- Processor success, repository failure và publish failure.
- Consumer delegates đúng processor.
- Producer nhận đúng topic nhưng test không gửi network.
- PostgreSQL repository test bằng mocked pgx boundary hoặc test SQL contract không cần database.
- Configuration validation.
- Cleanup task và context cancellation.
- Import/constructor không tạo external side effect.

## Tiêu chí nghiệm thu

```bash
gofmt -w .
go vet ./...
go test ./...
go test -race ./...
go build ./...
go mod tidy
git diff --exit-code -- go.mod go.sum
```

Nếu race detector không khả dụng trên môi trường, ghi rõ lý do nhưng vẫn chạy các lệnh còn lại.
README phải có architecture, commands, expected graph inventory và intentional negative cases.
Khi hoàn tất, trả về file đã tạo, lệnh đã chạy và kết quả; thực sự tạo đầy đủ repository.

