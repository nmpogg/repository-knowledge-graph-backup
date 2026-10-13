# Prompt tạo repository `rkg-fixture-bullmq-worker`

## Vai trò và mục tiêu

Bạn là kỹ sư senior Node.js/TypeScript chuyên hệ thống background job. Hãy tạo một
repository standalone tên `rkg-fixture-bullmq-worker` cho pipeline xử lý đơn hàng bằng
BullMQ. Project phải chạy/test được nhưng đồng thời là golden fixture để kiểm tra việc tái
sử dụng JavaScript/TypeScript language adapter cho một application không có HTTP entrypoint.

Không viết RKG adapter trong repo này. Không kết nối Redis, database hoặc network thật trong
test. Làm việc chỉ trong repository hiện tại và không commit dependency/build output.

## Stack bắt buộc

- Node.js LTS, TypeScript strict.
- BullMQ.
- Redis client chỉ thông qua BullMQ hoặc abstraction nhỏ; không cần Redis thật trong unit test.
- Vitest.
- ESLint.
- npm với `package-lock.json`.
- Chọn stable compatible versions và ghi phiên bản thực tế trong README.

## Domain chức năng

Worker xử lý vòng đời đơn hàng:

- Producer nhận yêu cầu và enqueue job `process-order`.
- Worker `order-processing` đọc job, gọi order service và lưu kết quả qua repository abstraction.
- Sau khi xử lý, enqueue event/job `send-order-email` sang queue email.
- Worker email consume queue email.
- Có retry/backoff và delayed job được khai báo tĩnh.
- Có một repeatable/scheduled cleanup job.
- Không cần HTTP server.

Payload chỉ chứa dữ liệu giả tối thiểu. Không log toàn bộ payload.

## Cấu trúc mong muốn

```text
src/
  index.ts
  config/
    environment.ts
    redis.ts
  queues/
    names.ts
    orderQueue.ts
    emailQueue.ts
  producers/
    orderProducer.ts
    emailProducer.ts
  workers/
    orderWorker.ts
    emailWorker.ts
    cleanupScheduler.ts
  services/
    orderService.ts
    emailService.ts
  repositories/
    orderRepository.ts
    inMemoryOrderRepository.ts
  domain/
    jobs.ts
    order.ts
  analysis-cases/
    positive/
      importedQueueName.ts
      typedWorkerFactory.ts
    negative/
      dynamicQueueName.ts
      reassignedWorker.ts
      unscopedPublish.ts
      shadowedBullmq.ts
tests/
```

Thêm configs, `.env.example`, `.gitignore`, README và test.

## Pattern static-analysis bắt buộc

### Queue identity

- Khai báo `ORDER_QUEUE = "order-processing"` và `EMAIL_QUEUE = "order-email"` ở module
  constants, mỗi constant được gán đúng một lần.
- Dùng trực tiếp literal ở ít nhất một case và imported constant ở case khác.
- Cùng queue name phải deduplicate thành một `MessageChannel` theo identity hợp lý.
- Redis URL/host không được dùng làm queue identity và không được đưa vào graph attributes.

### Publish

- Có `new Queue(...)` được resolve qua direct import.
- Có `queue.add("process-order", payload, options)` trong một callable rõ ràng.
- Có producer được bọc trong class và producer dạng function.
- Có delayed/retry options nhưng expected inventory chỉ yêu cầu channel và publish edge;
  payload/options không được lưu làm graph fact.
- Một call dùng queue name động phải tạo diagnostic, không được đoán channel.

### Consume

- Có `new Worker(ORDER_QUEUE, async (job) => ...)` với inline handler.
- Có `new Worker(EMAIL_QUEUE, namedProcessor)` với named function.
- Handler gọi service nội bộ để tạo call graph.
- Có factory trả về Worker với queue literal/imported constant, nhưng chỉ dùng pattern tĩnh,
  dễ resolve.
- `reassignedWorker.ts` cố ý gán receiver lại; không được tạo consume edge suy đoán.

### Scheduled/background behavior

- Tạo cleanup schedule bằng API BullMQ phù hợp với phiên bản đã chọn.
- Queue/job/schedule name phải tĩnh trong positive case.
- README nêu rõ schema RKG hiện tại có thể biểu diễn Callable + MessageChannel nhưng chưa chắc
  biểu diễn đầy đủ retry/schedule semantics; không ép schedule thành HTTP Endpoint.

### Configuration và security

- Đọc `REDIS_URL`, `ORDER_WORKER_CONCURRENCY`, `EMAIL_FROM` từ `process.env`.
- Parse và validate concurrency mà không lưu raw config value trong graph expectations.
- `.env.example` chỉ chứa placeholder.
- Có sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` trong test fixture và expected negative list.
- Không log job payload, Redis URL hoặc credential.

### Metadata/import cases

- Direct import, alias import, type-only import và relative import.
- Một local module/file không được giả danh package `bullmq`; negative case có local binding tên
  `Queue` hoặc `Worker` để kiểm tra shadowing mà không vi phạm module resolution.
- Package manifest/lock phải nhất quán.

## Expected inventory trong README

Liệt kê:

- Callables tạo queue, publish và process job.
- Hai MessageChannel dự kiến: `order-processing`, `order-email`.
- Publish/consume edges dự kiến cùng source path.
- Internal calls từ worker → service → repository.
- Configuration keys.
- Negative cases không được tạo edge/channel.
- Những thông tin không được lưu: payload, Redis URL, email address thực, retry body và secret.

## Thiết kế để test không cần Redis

- Tách queue construction/registration khỏi business logic.
- Unit test processor function trực tiếp với typed fake job tối thiểu.
- Mock BullMQ constructors/methods ở boundary test.
- Không khởi động Worker thật khi module được import.
- `src/index.ts` chỉ khởi động khi gọi explicit bootstrap; import module không có side effect network.

## Test bắt buộc

- Producer enqueue đúng queue/job name và không mutate payload.
- Order processor gọi service/repository và enqueue email.
- Email processor gọi email service.
- Configuration validation.
- Bootstrap wiring với mocks, không kết nối Redis.
- Test xác nhận import module không tự mở connection hoặc chạy worker.

## Tiêu chí nghiệm thu

```bash
npm ci
npm run lint
npm test -- --run
npm run build
npx tsc --noEmit
```

README phải giải thích đây là worker không có web app entrypoint, liệt kê expected graph facts,
intentional negative cases và các command. Khi hoàn tất, trả về danh sách file, command đã chạy,
kết quả và mọi sai khác. Hãy thực sự tạo repository hoàn chỉnh, không chỉ mô tả.

