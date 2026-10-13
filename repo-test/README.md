# Repository test prompts

Thư mục này chứa các prompt dùng để tạo những repository độc lập phục vụ kiểm thử
khả năng mở rộng language/framework adapter của Repository Knowledge Graph (RKG).
Các file ở đây là test-repository brief, không phải nguồn yêu cầu chuẩn tắc của RKG;
nguồn chuẩn tắc vẫn nằm trong `.aide/`.

## Danh sách prompt

| Thứ tự | Prompt | Mục tiêu chính |
|---|---|---|
| 1 | `01-react-typescript-frontend.md` | TypeScript/TSX, React Router, HTTP client, environment configuration |
| 2 | `02-bullmq-typescript-worker.md` | Tái sử dụng TypeScript parser cho worker, queue publish/consume |
| 3 | `03-spring-java-backend.md` | Java, Spring MVC, dependency injection, JPA và Kafka |
| 4 | `04-go-event-worker.md` | Go packages/interfaces, Kafka, PostgreSQL và scheduled worker |
| 5 | `05-nuxt4-fullstack.md` | Vue SFC, Nuxt file routing, auto-import và server routes |
| 6 | `06-polyglot-monorepo.md` | Nhiều application root và nhiều ngôn ngữ trong một snapshot |

## Cách sử dụng

1. Tạo một thư mục hoặc Git repository trống, nằm ngoài repository RKG này.
2. Sao chép nguyên nội dung của prompt tương ứng cho coding agent.
3. Yêu cầu agent làm việc chỉ trong repository đích và hoàn thành mọi tiêu chí nghiệm thu.
4. Chạy test/build của repository đích để xác nhận fixture tự nhất quán.
5. Đăng ký đường dẫn repository đích trong RKG và index nó mà không cài hoặc thực thi
   source của repository đích từ analyzer.
6. Chụp graph/report làm baseline trước khi phát triển adapter, sau đó so sánh với
   expected inventory trong prompt.

Nên tạo và kiểm thử năm repository độc lập trước. Chỉ tạo polyglot monorepo sau khi
các adapter tương ứng đã hoạt động riêng lẻ, nếu không sẽ khó xác định lỗi thuộc parser,
framework extractor, coordinator hay bước merge.

## Quy ước chung

- Các project cùng dùng domain order-commerce để sau này có thể ghép thành monorepo.
- Mỗi repo phải có lockfile được commit nhưng không commit dependency/build output.
- Case âm tính phải là source hợp lệ, trừ file được ghi rõ dùng để kiểm thử syntax error.
- Dynamic/ambiguous cases phải nằm trong code không chạy ở test bình thường.
- Chỉ dùng secret giả như `RKG_TEST_SECRET_DO_NOT_PERSIST`; không chứa credential thật.
- Không tạo file source khổng lồ hoặc binary. Scale corpus sẽ được sinh ở bước benchmark riêng.
- README của repo đích phải liệt kê các fact dự kiến để có thể xây golden graph về sau.

