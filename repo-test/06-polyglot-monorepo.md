# Prompt tạo repository `rkg-fixture-polyglot-commerce`

## Điều kiện tiên quyết

Chỉ dùng prompt này sau khi các repository React/TypeScript, BullMQ/TypeScript, Spring/Java và
Go worker đã được tạo và kiểm thử độc lập. Nếu một stack riêng lẻ chưa build/test ổn, dừng và
báo blocker thay vì che lỗi trong monorepo.

## Vai trò và mục tiêu

Bạn là kiến trúc sư/kỹ sư polyglot senior. Hãy tạo một monorepo standalone tên
`rkg-fixture-polyglot-commerce` chứa frontend, backend và hai worker tối giản nhưng hoạt động
nhất quán. Mục tiêu chính là kiểm thử RKG khi một manifest chứa nhiều language adapter, nhiều
application root, shared directories, package manifests và các giao tiếp xuyên service.

Không viết code RKG. Không sao chép dependency/build output từ các fixture khác. Làm việc chỉ
trong monorepo hiện tại. Không yêu cầu Docker/network cho unit test mặc định.

## Thành phần bắt buộc

```text
apps/
  web/
    # React + TypeScript frontend
services/
  orders/
    # Java + Spring Boot backend
workers/
  email/
    # TypeScript + BullMQ worker
  projection/
    # Go Kafka/PostgreSQL worker
contracts/
  asyncapi/
    order-events.yaml
  openapi/
    orders-api.yaml
scripts/
  verify-all.*
README.md
```

Mỗi component phải có manifest, lock/checksum file, README ngắn và test riêng. Không tạo một root
package manager giả để cố quản lý Java/Go. Có thể dùng npm workspaces chỉ cho các project Node
nếu không làm ownership `package.json` mơ hồ; nếu dùng, giải thích rõ trong root README.

## Luồng kiến trúc chung

1. React web gọi `GET/POST /api/orders` của Spring service.
2. Spring service lưu `commerce.orders` và publish `orders.events`.
3. Go projection worker consume `orders.events`, ghi `commerce.order_projection`, publish
   `orders.projection.updated`.
4. TypeScript email worker consume một queue/event `order-email` do application flow tạo.

Không cần các process thật sự giao tiếp trong test mặc định; contract names phải thống nhất qua
constants/spec fixtures và test contract nhẹ.

## Yêu cầu giữ fixture nhỏ

- Mỗi app/service/worker chỉ giữ subset tối thiểu chứng minh architecture flow.
- Tổng số source file mục tiêu 80–150, không nhân bản hàng nghìn file.
- Không thêm Kubernetes/Terraform trừ vài manifest text thật sự cần cho context; hạ tầng không
  phải mục tiêu vòng đầu.
- Không commit generated OpenAPI clients, compiled class, JS bundle hoặc Go binary.

## Multi-language và file ownership cases

- Có `.ts`, `.tsx`, `.java`, `.go`, `.vue` chỉ khi thật sự thêm Nuxt (mặc định không thêm Nuxt).
- Có `package.json`, `pom.xml`, `go.mod` ở đúng subroot.
- Không để Java adapter claim Node manifest hoặc ngược lại.
- Shared parent directories phải tạo đúng một Directory node trong graph.
- Unknown files như Markdown/YAML phải được report rõ nhưng không biến thành SourceUnit nếu chưa
  có adapter tương ứng.
- Có generated directories giả rỗng hoặc `.gitkeep` chỉ khi cần kiểm tra ignore; ưu tiên README
  mô tả hơn là commit output.

## Nhiều application roots

Root README phải khai báo inventory ứng dụng:

| App key | Root | Language | Framework | Entrypoint intent |
|---|---|---|---|---|
| `web` | `apps/web` | TypeScript | React | `src/main.tsx` |
| `orders` | `services/orders` | Java | Spring Boot | application class |
| `email-worker` | `workers/email` | TypeScript | BullMQ | explicit bootstrap |
| `projection-worker` | `workers/projection` | Go | worker | `cmd/.../main.go` |

Fixture phải làm lộ giới hạn của cấu hình một `app_module:app_symbol`; không workaround bằng cách
giả vờ toàn monorepo chỉ có một app. Expected analyzer behavior sau khi core mở rộng là selection
theo root/language/framework.

## Cross-service linking expectations

Root README phải tách hai mức:

### Facts adapter-local

- React outbound HTTP dependency/call site.
- Spring REST Endpoint và handler.
- Spring publish `orders.events`.
- Go consume `orders.events` và publish `orders.projection.updated`.
- BullMQ worker consume `order-email`.
- Data resources theo từng service.

### Facts cần post-merge linker

- React relative `/api/orders` ↔ Spring endpoint.
- Producer/consumer dùng cùng channel identity xuyên ngôn ngữ.
- OpenAPI/AsyncAPI contract ↔ code implementation nếu feature đó được thêm.

Không yêu cầu language adapter tự nhìn representation của ngôn ngữ khác. Không tạo link nếu chỉ
trùng tên mơ hồ; linker phải dựa trên normalized method/path/channel và evidence.

## Positive cases bắt buộc

- Cùng topic literal `orders.events` xuất hiện ở Java producer và Go consumer.
- Cùng REST method/path xuất hiện trong React API client và Spring controller.
- Cùng queue `order-email` xuất hiện ở producer phù hợp và BullMQ consumer.
- Hai language có file trong cùng logical feature directory hoặc shared ancestor để kiểm tra
  Directory deduplication.
- Từng component có internal call chain rõ ràng.
- Mọi fact dự kiến có source path và line/rule intent mô tả được.

## Negative cases bắt buộc

- Một dynamic HTTP URL không được link tới endpoint.
- Một dynamic topic/queue không được merge với literal channel.
- Hai endpoints cùng path nhưng khác method để kiểm tra identity.
- Hai resources cùng table name nhưng khác schema/service context.
- Hai symbols cùng simple name ở hai language không được merge thành một entity.
- Một unsupported file extension và một syntax-error fixture cho mỗi language, nhưng không làm
  build mặc định thất bại.
- Secret sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` xuất hiện trong test fixtures và không được
  lưu vào graph/report/log.

## Contracts

- OpenAPI document tối thiểu mô tả endpoints thực sự có trong Spring service.
- AsyncAPI document tối thiểu mô tả `orders.events` và `orders.projection.updated`.
- Specs phải validate bằng tool/library phù hợp nếu có thể mà không cần network.
- Không generate source client/server từ specs; source và spec được viết tường minh để tránh
  generated noise.
- README nêu specs là evidence bổ sung, không tự động thắng source khi hai bên mâu thuẫn.

## Test và command orchestration

Mỗi component giữ command native:

- Web/email worker: npm lint/test/build/typecheck.
- Spring: Maven wrapper test/verify.
- Go: fmt/vet/test/race/build.

Root `scripts/verify-all` phải:

- Fail fast và trả exit code khác 0 khi component fail.
- Không cài global package.
- Không khởi động server, broker hoặc database.
- Không chứa absolute host path.
- Chạy được trên shell/documented platform đã chọn; nếu cần Windows equivalent, ghi trong README.

Không tạo orchestration phức tạp chỉ để chạy song song.

## Expected inventory chuẩn

Tạo `expected/README.md` và các file JSON/YAML dễ đọc bằng người:

```text
expected/
  applications.yaml
  technologies.yaml
  entities.yaml
  edges.yaml
  diagnostics.yaml
  prohibited-values.txt
```

Các expected file:

- Dùng semantic keys/path/qualified names, không dùng RKG hash ID.
- Phân biệt exact expected, optional/detected-only và prohibited fact.
- Ghi source evidence path + line hoặc marker comment ổn định.
- Bao gồm adapter-local facts và post-merge facts ở section riêng.
- Không chứa absolute path, source body, payload hoặc credential.

Thêm marker comments ổn định trong source khi cần, ví dụ `RKG_EXPECT: spring-create-order`, nhưng
không lạm dụng comment thay cho code semantics.

## Performance corpus profile

Không commit scale corpus lớn. Thêm script deterministic có thể sinh vào ignored directory:

- 100, 1.000 hoặc 9.000 source-like files từ template an toàn.
- Tên/path/content deterministic theo seed cố định.
- Không thực thi generated files.
- Có command cleanup chỉ xóa đúng generated directory đã biết.
- Generated directory nằm trong `.gitignore`.

README cảnh báo script này chỉ phục vụ scanner benchmark và không phải source production.

## Security và isolation

- Không credential thật.
- Không network trong test mặc định.
- Không log raw payload/config value.
- Không absolute host paths trong expected output.
- Importing modules/packages không tự mở connection hoặc spawn long-running process.
- Mọi bootstrap phải explicit tại application entrypoint.

## Tiêu chí nghiệm thu

1. Mỗi component pass native lint/test/build/typecheck.
2. Root verification script pass từ clean checkout sau khi dependencies đã cài theo README.
3. OpenAPI/AsyncAPI specs khớp constants/routes trong code.
4. Expected inventory hoàn chỉnh và không chứa hash ID/absolute path/secret.
5. Không commit dependency/build/generated scale corpus.
6. Root README mô tả application roots, technology matrix, communication flow, commands,
   expected graph và intentional negative cases.

Khi hoàn tất, trả về:

- Cây thư mục tóm tắt.
- Phiên bản tool/framework thực tế.
- Lệnh đã chạy và kết quả từng component.
- Các expected inventory files đã tạo.
- Mọi sai khác hoặc giới hạn còn lại.

Không chỉ mô tả cách làm; hãy thực sự tạo monorepo đầy đủ và xác minh nó.

