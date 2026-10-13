---
uid:
key: CMP-RKG-TRANSPORT
type: component
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 7
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {realizes: [CAP-RKG-001, CAP-RKG-002, CAP-RKG-003], constrained_by: [NFR-RKG-SEC-001]}
classification: internal
ai_assisted: true
---
# CMP-RKG-TRANSPORT — API and CLI transport

Revision 7 aligns the heading with the key and filename.
FastAPI và CLI validate/serialize input-output rồi gọi cùng application services
cho cả ba capability (repository/index analysis, graph/snapshot explore, conversation/Q&A).
Transport không định nghĩa lại domain enums/limits và không chứa extraction,
graph-write hay provider logic.

Runtime hiện tại tách hai process loopback: `rkg serve` chạy API bằng uvicorn;
frontend Vite chạy riêng. API không mount static frontend. CORS chỉ phản chiếu
origin loopback trên port khác. `ADR-2026-003` vẫn ghi quyết định transport
phục vụ static asset cùng origin. Server hiện tại chưa làm điều đó. Revision
này không lật ADR; giữ hay đổi quyết định đó còn chờ architecture decision.

Revision 5 ghi `status: approved`. `approval-005` pin revision 4. Revision 6 là
sửa tài liệu cho khớp runtime và chưa có approval mới.

## Internal structure

`create_app` dựng FastAPI, session gate cho mutation `/api/*`, và CORS loopback.
CLI `rkg serve` gọi uvicorn trên loopback, một worker. Handler chỉ validate và
gọi service. Không có static mount cho frontend.

## Sequence

Handler kiểm tra session với mutation `/api/*`, validate input, rồi gọi service
bên trong `call_when_idle`. Đọc graph và mutation catalog đều chờ writer lock
của index job. Job progress là polling `Retry-After`, không phải conditional
request.

## Failure mode

Input không hợp lệ trả `422`. Session/Origin/Host sai trên mutation trả `401`.
Job đang giữ writer trả `409 index_job_busy` và không tạo job thứ hai. Không có
process thứ hai để phục vụ frontend từ cùng origin.

## Process and progress model

MVP chạy đúng một application process/worker để chỉ có một Kùzu writer owner và
job coordinator. Thread/task nội bộ vẫn được phép nếu tuân thủ single-writer và
pinned-reader guards. Multi-process workers chỉ được mở sau một ADR và concurrency
test riêng.

API v1 expose repository CRUD và snapshot lifecycle, dùng bounded polling cho job
progress và response hoàn chỉnh cho Q&A theo
`API-RKG-CORE-v1`; SSE/WebSocket và token streaming ngoài phạm vi MVP.

## Transaction boundary

Transport kiểm tra input rồi gọi application service. Không mở transaction storage
và không tự publish snapshot.

## Idempotency

Submit index khi còn job chưa kết thúc trả `409 index_job_busy` và không tạo job
thứ hai. Idempotency của turn nằm ở `client_request_id` trong
`CMP-RKG-CONVERSATION`, không phải bằng cách gọi lại provider từ mép HTTP.

## Concurrency

Một process sở hữu writer duy nhất. Handler không mở job thứ hai và không mở
writer thứ hai.
