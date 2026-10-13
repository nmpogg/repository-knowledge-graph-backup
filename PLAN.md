# Kế hoạch làm song song cho hai người

> Bảng điều phối hai người dừng tại mốc 2026-09-28, hết T-023. Task `030`–`047`, Change Set `002`–`014` và epic `006` chỉ có trạng thái trong `.aide/`. File này không phải artifact vòng đời. Không thêm tham chiếu từ `.aide/` đến file này.

## Điểm xuất phát

- T-001 đã `done`: Python/Kùzu/DDL và frontend React/Vite đã có nền tảng.
- T-002 đã `done`: domain schema, ID, DTO và golden fixtures; handoff ở
`src/rkg/domain/README.md`.
- T-017 đã `done`: MVP UI mock (onboarding/job/Explorer/export); evidence
`DIARY-TASK-RKG-017` / `TEST-RKG-UI-MVP-MOCK-001`.
- T-025 đã `done`: repo/snapshot management guards trên mock; evidence
`DIARY-TASK-RKG-025` / `TEST-RKG-UI-REPO-MGMT-MOCK-001`.
- T-013 đã `done`: Kùzu storage + atomic snapshots; evidence
`DIARY-TASK-RKG-013` / `TEST-RKG-STORAGE-SNAPSHOTS-001`. Handoff storage/graph
interface cho T-015 ở `src/rkg/storage/README.md` và `src/rkg/graph/README.md`.
- T-014 đã `done`: search/BFS/context services; evidence `DIARY-TASK-RKG-014` /
`TEST-RKG-GRAPH-READS-001`. Benchmark p95 (AC-037/062) còn lại cho T-022.
- T-015 đã `done`: index job và CLI; evidence `TEST-RKG-INDEX-JOB-CLI-001`.
- T-016 đã `done`: FastAPI transport; evidence `DIARY-TASK-RKG-016` /
`TEST-RKG-CORE-API-001`. Handoff ở `src/rkg/api/README.md`.
- T-003, T-004, T-005, T-006, T-007 đã `done`. T-007 có evidence `DIARY-TASK-RKG-007` / `TEST-RKG-PKG-INVENTORY`.
- T-008 đã `done`: detection/selection và app candidates; evidence `DIARY-TASK-RKG-008` / `TEST-RKG-DETECT-001`.
- T-009 đã `done`: FastAPI adapter route/DI; evidence `DIARY-TASK-RKG-009` / `TEST-RKG-FASTAPI-ADAPTER-001`.
- T-010 đã `done`: SQLAlchemy data-access adapter; evidence `DIARY-TASK-RKG-010` / `TEST-RKG-SQLALCHEMY-ADAPTER-001`.
- T-011 đã `done`: aiokafka messaging adapter; evidence `DIARY-TASK-RKG-011` / `TEST-RKG-AIOKAFKA-ADAPTER-001`.
- T-012 đã `done`: config key và HTTP origin; evidence `DIARY-TASK-RKG-012` / `TEST-RKG-CONFIG` / `TEST-RKG-HTTP-INVENTORY`.
- T-018 đã `done`: conversation/turn persistence; evidence `DIARY-TASK-RKG-018` /
`TEST-RKG-CONVERSATION-STATE-001`. Handoff ở `src/rkg/conversations/README.md`.
- T-019 đã `done`: LLM provider interface/adapter (OpenRouter); evidence
`DIARY-TASK-RKG-019-r3` / `TEST-RKG-OPENROUTER-LIVE-001`. HTTP mapping thuộc T-021.
- T-020 đã `done`: history-aware grounded Q&A; evidence `DIARY-TASK-RKG-020-r2` /
`TEST-RKG-GROUNDED-QA-002`. HTTP routes vẫn thuộc T-021. Handoff ở
`src/rkg/conversations/README.md`.
- **Cửa sổ hiện tại:** T-022 và T-023 đã `done`. Finding KPI/performance của
T-022 được chuyển trong handoff T-023. `EPIC-005-TEAM-RKG` vẫn `draft`.
- Theo `.aide/`: `GATE-RKG-SCOPE`, `ARCHITECTURE`, `UIUX`, `CONTRACT` đều `pending` trên Change Set / candidate baseline `BL-CHG-RKG-2026-001` r3. Approval lịch sử (`approval-001`…`006`) không khóa revision hiện tại; `OQ-RKG-006` (signer identity) còn mở. Việc ký gate theo quy trình riêng, không được suy ra từ trạng thái của bảng này.

## Quy tắc phối hợp

1. **Một task có một người chịu trách nhiệm chính.** Người còn lại review tại điểm bàn giao, không cùng sửa một task hoặc một file trên hai nhánh khi chưa thống nhất rõ phần việc.
2. **Chỉ bắt đầu phần triển khai của task khi các `depends_on` đã `done`.** Có thể đọc contract, chuẩn bị fixture hoặc review trước; không coi việc chuẩn bị đó là task hoàn thành. T-025 chỉ đóng sau T-017.
3. **Bàn giao bằng mã, test và ghi chú ngắn:** commit/nhánh, interface và fixture đã chốt, lệnh kiểm tra cùng kết quả, thay đổi contract nếu có, việc còn vướng. Người nhận xác nhận interface trước khi xây tiếp. Không merge hai nhánh cùng thay một contract khi chưa thống nhất.
4. **Nguồn sự thật cho tiến độ là frontmatter của TASK.** Khi hoàn tất, kiểm chứng trên cây mã hiện tại và ghi evidence theo quy định repo trước khi chuyển `done`. Không dùng ô đánh dấu trong PLAN để thay status chính thức.
5. **Giữ ranh giới file:** A sở hữu `src/rkg/domain/`, `ingestion/`, `parsing/`, `adapters/`, `detection/`, `extractors/`, `resolution/`, `jobs/`, `cli/` và fixture/test tương ứng, trừ module và test của T-010, T-011, T-012. B sở hữu các module đó cùng `src/rkg/storage/`, `graph/`, `api/`, `conversations/`, `frontend/` và fixture/test tương ứng. `src/rkg/llm/` thuộc A. File dùng chung như `pyproject.toml`, config chung, DDL, contract adapter và API contract cần một PR riêng hoặc sự đồng ý của cả hai trước khi sửa.

## Phân công và điều kiện bắt đầu


| Task                | Người chính             | Làm gì / điểm bàn giao                                                                        | Phải đợi                                                       |
| ------------------- | ----------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| T-002               | **B**                   | Domain schema, ID, DTO và golden fixtures; bàn giao interface/fixtures ổn định cho A          | T-001 (**đã xong**); **đã `done`**                             |
| T-003               | **A**                   | Local source loader, manifest, giới hạn file và bảo vệ path/symlink                           | T-002 (**đã xong**); **đã `done`**                             |
| T-004               | **A**                   | Contract adapter và conformance suite                                                         | T-002, T-003 (**đã xong**); **đã `done`**                      |
| T-005 → T-006       | **A**                   | Python AST/scope, rồi import/call/class resolution                                            | T-004 → T-005 (**đã xong**); **đã `done`**                     |
| T-007 → T-008       | **A**                   | Metadata/package inventory, rồi detection/selection                                           | Cả hai **đã `done`**                                           |
| T-009               | **A**                   | FastAPI framework adapter                                                                     | T-006 + T-008 (**đã xong**); **đã `done`**                     |
| T-010, T-011, T-012 | **B**                   | SQLAlchemy, aiokafka và config/HTTP extraction                                                | Cả ba **đã `done`**                                            |
| T-013               | **B**                   | Kùzu storage, repository và snapshot transaction; bàn giao storage interface cho A            | T-002 (**đã xong**); **đã `done`**                             |
| T-014               | **B**                   | Search, traversal và bounded context services                                                 | T-013 (**đã xong**); **đã `done`**                             |
| T-015               | **A**                   | Ghép analyzer với storage thành index job và CLI; bàn giao service interface/job states cho B | T-004, T-009/010/011/012, T-013 (**đã xong**); **đã `done`**   |
| T-016               | **B**                   | Core FastAPI transport, repository/snapshot/job/graph/context endpoints                       | T-014, T-015 (**đã xong**); **đã `done`**                      |
| T-017               | **B**                   | MVP UI dùng mock client và fixtures đúng contract; bàn giao UI shell/client interface         | T-001 (**đã xong**); **đã `done`**                             |
| T-025               | **B**                   | UI quản lý repository/snapshot dùng mock, gồm conflict/confirm/guards                         | T-001, T-017 (**đã xong**); **đã `done`**                      |
| T-024               | **B**                   | Thay mock bằng live API, kiểm tra onboarding/index/Explorer/repository/snapshot               | T-016, T-017, T-025 (**đã xong**); **đã `done`**               |
| T-018               | **B**                   | Conversation persistence và state                                                             | T-013, T-014 (**đã xong**); **đã `done`**                      |
| T-019               | **A**                   | LLM provider interface/adapter và live evaluation; bàn giao provider interface cho T-020      | T-002, T-014 (**đã xong**); **đã `done`**                      |
| T-020               | **A**                   | History-aware grounded Q&A; bàn giao service interface cho T-021                              | T-018, T-019 (**đã xong**); **đã `done`**                      |
| T-021               | **B**                   | Conversation API và UI                                                                        | T-016, T-024, T-020 (**đã xong**); **đã `done`**               |
| T-022               | **A**, B hỗ trợ UI/eval | Pilot, eval, benchmark; A tổng hợp evidence, B kiểm tra luồng UI                              | T-015, T-024, T-021; OQ-RKG-002 đã chọn; **đã `done`**         |
| T-023               | **B**, A review         | Runbook và handoff cuối                                                                       | T-022 (**đã xong**); **đã `done`**                             |


## Lịch chạy hai luồng

Giữ một hàng **Đã xong**; khi tiến độ đổi, bổ sung task đã đóng vào hàng đó và dịch nội dung hàng **Ngay bây giờ** — không xóa lịch sử trong hàng đã xong.


| Mốc                         | Người A                                                                     | Người B                                                                     | Điểm đồng bộ                                                                                                         |
| --------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Đã xong**                 | T-002, T-003, T-004, T-005, T-006, T-007, T-008, T-009, T-015, T-019, T-020, T-022 | T-010, T-011, T-012, T-013, T-014, T-016, T-017, T-018, T-021, T-023, T-024, T-025 | T-023: `DIARY-TASK-RKG-023` / `TEST-RKG-FINAL-REGRESSION-001`. Finding KPI/performance vẫn mở. |
| **Ngay bây giờ**            | Review handoff T-023 và finding còn mở                                     | Đã bàn giao runbook; chờ A review                                           | T-022 và T-023 đã `done`. Epic M5 vẫn chờ duyệt người.                                                               |
| **Tích hợp**                | Review T-021                                                                | T-021 (**đã xong**)                                                         | Conversation API và UI đã nối vào grounded Q&A.                                                                      |
| **Hội thoại và nghiệm thu** | T-022 (**đã xong**); review finding và handoff                              | T-022 hỗ trợ UI → T-023 (**đã xong**)                                       | Handoff đã ghi finding mở. Không suy ra waiver KPI hay NFR performance.                                             |


## Xử lý xung đột và thay đổi kế hoạch

- Nếu một task làm lộ chỗ thiếu trong DTO, DDL hoặc API contract, người phát hiện ghi rõ thay đổi đề xuất và AC bị ảnh hưởng; hai người thống nhất trước khi sửa file chung. Người sở hữu task tạo PR thay đổi contract, người kia review trước khi tiếp tục phần phụ thuộc.
- Không giả định T-009–T-012 hoặc T-017/T-025 có thể `done` cùng lúc chỉ vì đtang làm song song. Mỗi task chỉ đóng sau đúng dependency và evidence của chính nó.
- Khi một nhánh bị chặn, chuyển sang **task đã đủ dependency** trong cột của mình hoặc review/fixture cho điểm bàn giao kế tiếp; không bỏ qua dependency để giữ người bận.
- Cập nhật bảng này khi phân công đổi: **bổ sung** vào hàng “Đã xong” và dịch “Ngay bây giờ”; không xóa task đã ghi trong hàng đó, không sửa lịch sử approval/baseline, và không dùng file này để tuyên bố gate đã đóng.

