# Repository Knowledge Graph

> **Docs-first:** Nguồn chuẩn tắc nằm tại [`.aide/`](.aide/README.md) (`AGENTS.md`).
> Thư mục `docs/` sản phẩm đã gỡ; chỉ còn
> [`docs/reference/agentic-sdlc/`](docs/reference/agentic-sdlc/) làm tham khảo
> workflow. Runbook dưới đây là hướng dẫn vận hành local, không thay frontmatter
> task hay gate.

Repository Knowledge Graph phân tích một thư mục source local thành graph kiến trúc
có bằng chứng. Index và truy vấn graph chạy khi không có LLM. Hỏi đáp có citation
là lớp tùy chọn phía trên snapshot đã pin.

## Trạng thái bàn giao

Nguồn tiến độ là frontmatter trong [`.aide/lifecycle/tasks/`](.aide/lifecycle/tasks/).
Trên cây hiện tại, `TASK-RKG-000` đến `TASK-RKG-041` đã `done`, gồm index/CLI,
API loopback, UI live, hội thoại và pilot/eval (`TASK-RKG-022`).
`TASK-RKG-042` đến `TASK-RKG-047` đang `in_progress` trên `CHG-RKG-2026-009` đến
`CHG-RKG-2026-014`. `TASK-RKG-048` đến `TASK-RKG-055` đang `in_progress` trên
`CHG-RKG-2026-015` đến `CHG-RKG-2026-022` (backfill hồ sơ cho adapter và liên kết
HTTP tĩnh đã có trên cây).

Runbook này thuộc `TASK-RKG-023`. Kết quả regression, phạm vi, giới hạn và rủi
ro còn lại nằm ở `DIARY-TASK-RKG-023` và `TEST-RKG-FINAL-REGRESSION-001`.
Các finding mở của pilot/eval vẫn mở: census fixture chuẩn cho KPI-RKG-001,
phán quyết mẫu pilot cho KPI-RKG-002, và p95 context của NFR-RKG-PERF-001.
`EPIC-005-TEAM-RKG` vẫn `draft` cho đến khi người duyệt đóng finding và ký
release readiness.

Source chỉ là thư mục local đã có trên máy chạy RKG. Tạo repository chỉ ghi
metadata. Graph xuất hiện sau khi job index publish snapshot.

## Cài đặt

| Thành phần | Phiên bản đã pin |
| --- | --- |
| CPython | **3.12.14** (`.python-version`); `requires-python = ">=3.12,<3.13"` |
| Package manager Python | [uv](https://docs.astral.sh/uv/) + `uv.lock` |
| Kùzu (Python) | **0.11.3** |
| Node.js | **22** LTS (`.nvmrc`); `engines` cho phép `>=22 <25` |
| Package manager JS | **npm** + `frontend/package-lock.json` |

Từ root repo:

```bash
uv sync --group dev
uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"
uv run python -c "import rkg; import importlib.metadata as m; assert m.version('kuzu')=='0.11.3'"
```

Frontend:

```bash
cd frontend
npm ci
```

Database mặc định là `.rkg/graph` trong thư mục làm việc (`--db` hoặc
`RKG_DB_PATH`). Đó là dữ liệu local của máy vận hành. Schema được migrate khi
mở storage.

## Đường dẫn local

`--allow-root` là danh sách gốc do người vận hành sở hữu. Có thể lặp flag.
Khi bỏ qua, gốc được phép là thư mục hiện tại. Request không được tự khai
báo gốc được phép.

```powershell
uv run rkg --allow-root D:\sources repository create --name "orders" --path D:\sources\orders
```

`--path` phải là thư mục nằm trong một `--allow-root` đã khai báo.
Muốn mở rộng đường dẫn được phép, kể cả cả một ổ đĩa, truyền gốc đó vào
`--allow-root` rồi chạy lại lệnh (tạo repository, index hoặc serve):

```powershell
uv run rkg --allow-root <goc> serve
```

`<goc>` là thư mục cha hoặc gốc ổ, dạng `X:\`. Cùng một cờ lặp lại khi cần
nhiều gốc. Server đang chạy phải khởi động lại với cờ này thì UI mới nhận
gốc mới.
`--source-root`, khi có, là thư mục con tương đối dùng làm gốc quét.
Đường dẫn UNC, device path, thư mục ngoài root, symlink/junction thoát khỏi
root canonical bị từ chối trước khi đọc nội dung. Loader bỏ symlink/junction
nằm trong root để tránh vòng lặp. Source không được import, cài dependency
hay thực thi.

Giới hạn quét mặc định: 10.000 file và 2 MiB/file. Pattern bỏ qua mặc định
gồm `.git/**`, `.venv/**`, `**/__pycache__/**`, `node_modules/**`,
`**/.cache/**`, `**/.pytest_cache/**` và `**/.ruff_cache/**`. Các mẫu cache
bỏ qua cả thư mục để scanner không đi vào cache không đọc được.
Đặt lại bằng `--max-files` và `--max-file-bytes` lúc tạo hoặc cập nhật
repository. Quá số file thì job dừng với `file_limit_exceeded`. File quá lớn
bị bỏ qua và ghi `file_too_large` trong báo cáo scan.

## Index

Một process chỉ chạy một index job tại một thời điểm. Job đọc metadata đã lưu,
quét source, publish snapshot bất biến và đặt snapshot đó thành active của đúng
repository.

```powershell
uv run rkg --allow-root D:\sources index --repository repo_id
```

Thoát `0` khi `succeeded` hoặc `succeeded_with_warnings`. Thoát `1` khi job lỗi
hoặc khi CLI in `error_code`. Job thứ hai trong lúc job đầu chưa xong trả
`index_job_busy` (HTTP `409` nếu gọi qua API). Mở lại process sẽ đánh dấu job
còn treo là `index_interrupted`; graph đã publish giữ nguyên.

Re-index tạo snapshot mới. Snapshot đã publish không bị sửa nội dung.

## Serve và UI

`rkg serve` chỉ bind `127.0.0.1`, một worker. Host khác, worker khác hoặc port
ngoài 1–65535 trả `serve_config_invalid`.
Uvicorn in thông báo khởi động và địa chỉ đang lắng nghe. Mỗi HTTP request
được log theo method, route mẫu, status và thời gian xử lý; query, body và
giá trị ID trong URL không được ghi vào log.

Tạo `.env` ở root repo từ `.env.example` (nếu đã có `.env` thì bổ sung các
biến còn thiếu). CLI tự đọc cấu hình backend từ file này; Vite đọc các biến
`VITE_` từ cùng file. Đặt `RKG_SESSION_TOKEN` và `VITE_RKG_SESSION` cùng một
chuỗi; `VITE_RKG_CLIENT=live` bật kết nối UI với API. `.env` được Git bỏ qua.
Nếu token backend trống, server từ chối khởi động.

```powershell
uv run rkg serve

# terminal khác, trong frontend/
npm run dev
```

Muốn phân tích source ngoài thư mục repo, mở rộng gốc được phép rồi serve:
`uv run rkg --allow-root <goc> serve`. Nếu PowerShell trên máy chặn
`npm.ps1`, chạy `npm.cmd run dev` thay cho `npm run dev`.

Mở `http://127.0.0.1:5173`. Để trống `VITE_RKG_API_BASE` để Vite proxy `/api`
tới `127.0.0.1:8000` (`RKG_API_UPSTREAM` đổi target đó). CORS chỉ phản chiếu
origin loopback. Mutation và `POST /context` cần header `X-RKG-Session` cùng
`Host` loopback.

Luồng UI: tạo repository bằng đường dẫn tuyệt đối nằm trong `--allow-root`,
bấm index, đợi job tới trạng thái terminal, rồi mở Explorer trên snapshot
active. Hội thoại nằm ở luồng Ask: tạo hội thoại trên snapshot đang pin, xem
lịch sử, gửi câu hỏi tiếp và xóa sau khi xác nhận.

Client mặc định của frontend là mock. `.env.example` đặt `VITE_RKG_CLIENT=live`
để UI gọi API sau khi sao chép thành `.env`.

## Log terminal backend

```bash
uv run rkg serve --log-level debug
```

Restart backend với lệnh này để bật log đầy đủ cho chatbot: request/turn ID,
chu kỳ lượt, stage, thời gian, số model/graph calls, input/output token,
request gửi provider, phản hồi HTTP/model và chi tiết JSON/schema/graph validator
(tên rule, vị trí trường, giá trị nhận được và điều kiện mong đợi).
Debug hiển thị nội dung model ngay trong terminal theo lựa chọn của operator;
không tự ghi file hoặc thêm vào API/history/evidence. Các key đang cấu hình trên
server được thay bằng `[masked]`; Authorization header không thuộc trace model.
`--log-level info` là mặc định, hiển thị lifecycle/counters/rejection, không in
nội dung model. Log framework giữ level info. Giữ các tham số `--db`,
`--allow-root`, `--port` đang dùng khi restart.

## LLM

Chatbot hỗ trợ **OpenRouter và OpenAI trực tiếp**. Cấu hình trong `.env` tại
repository root hoặc môi trường process server. `RKG_LLM_PROVIDER` chọn provider;
khi không đặt biến này, mặc định là `openrouter` để giữ cấu hình cũ.

```dotenv
# OpenAI trực tiếp
RKG_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

Để dùng OpenRouter, đặt `RKG_LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY` và
`OPENROUTER_MODEL` (mặc định `openai/gpt-4o-mini`). OpenAI mặc định `gpt-4o-mini`;
model được chọn cần hỗ trợ strict JSON-schema Structured Outputs. Restart backend
sau khi đổi cấu hình. Key chỉ đặt phía server, không dùng biến `VITE_`.

Thiếu hoặc trống key của provider đã chọn thì lượt hỏi trả `503 llm_disabled`,
kể cả khi provider còn lại có key. Không tự chuyển provider khi gặp lỗi.
Selector khác `openai`/`openrouter` khiến server từ chối khởi tạo bằng
`llm_invalid_request`. Search, Explorer và context JSON chạy khi LLM bị tắt.

Mặc định không áp trần ứng dụng cho số lần gọi model, input/output token, số truy
vấn graph, tổng thời gian lượt và số ký tự câu hỏi. Các giới hạn context, history,
retrieval, schema và grounding vẫn giữ. Nhà cung cấp vẫn có giới hạn riêng.
Provider lỗi trả `502` với `llm_budget_exceeded`, `llm_malformed_response` hoặc
`llm_provider_error`; timeout mạng là `504 llm_timeout`. Các lỗi này không đổi
focus đã commit.

Ở level info, key, prompt, câu trả lời và exception thô không ghi vào log vận hành. Với lỗi
model, backend ghi diagnostic dạng `event=llm_rejected stage=narrative
reason=invalid_schema error_code=llm_malformed_response`. Stage là `read_plan`,
`narrative` hoặc `narrative_grounding`; reason chỉ là mã trong allowlist, không
chứa input/output của model. Lượt lỗi cũ chỉ có mã chung; gửi một lượt mới sau khi
restart backend để có diagnostic. UI không hiển thị coverage cho lượt lỗi.

Tokenizer `o200k_base` nằm trong package, có kiểm SHA-256 lúc nạp.

## Lịch sử hội thoại

Tạo hội thoại pin `snapshot_id`, hoặc snapshot active nếu bỏ trống. Publish
sau đó không đổi pin. Mỗi lượt cần `client_request_id` và `expected_revision`
dương. Sai revision hoặc cùng request id với nội dung khác là
`409 conversation_conflict`. Cùng nội dung thì trả lại lượt đã lưu, không gọi
provider lần nữa.

Ngữ cảnh gửi provider giữ tối đa 6 lượt đã hoàn thành và 4.000 token lịch sử.
Lượt cũ bị cắt trước; focus có cấu trúc vẫn giữ. Response của lượt đang gửi có
`history_truncated` khi cửa sổ bị cắt. Cờ đó nằm trên response, không được tính
lại khi tải trang lịch sử.

Xóa hội thoại trong lúc còn lượt `pending` trả `409 conversation_busy`.
Sau khi process khởi động lại, lượt `pending` còn sót thành `interrupted`;
lịch sử và focus đã commit giữ nguyên. Đọc hội thoại khi snapshot pin không
còn trả `410 snapshot_unavailable` và không chuyển hội thoại sang snapshot khác.

## Giữ và xóa dữ liệu

Xóa snapshot bị từ chối khi snapshot còn active (`snapshot_active`) hoặc còn
reader trong process / còn hội thoại pin (`snapshot_in_use`). Xóa repository
bị từ chối khi còn job chưa terminal (`repository_busy`) hoặc còn reader /
hội thoại (`repository_in_use`). Xóa repository đã qua guard thì xóa snapshot
và graph con của repository đó.

Thứ tự vận hành để bỏ một snapshot cũ:

1. Kích hoạt snapshot khác nếu snapshot sắp xóa đang active.
2. Xóa các hội thoại còn pin snapshot đó.
3. `rkg snapshot delete --repository <id> <snapshot_id>` khi không còn lượt đọc.

`cleanup_snapshots(storage, repository_id)` trong `rkg.conversations` xóa các
snapshot không active, không bị reader pin và không bị hội thoại tham chiếu,
bỏ qua snapshot bị guard. Hàm này dùng trong process; CLI và HTTP hiện chưa
có lệnh gọi nó. Người vận hành xóa từng snapshot bằng lệnh ở trên.

Cập nhật repository cần `--expected-revision`. Path gốc của repository đã tạo
không đổi (`repository_source_immutable`).

## Xử lý sự cố

| `error_code` | Việc cần làm |
| --- | --- |
| `source_outside_allowed_roots` | Mở rộng đường dẫn: `uv run rkg --allow-root <goc> serve` (hoặc create/index) với `<goc>` bao thư mục đó, rồi tạo/index lại. |
| `source_path_invalid`, `source_not_directory`, `source_root_invalid` | Kiểm tra `--path` là thư mục thật và `--source-root` nằm trong đó. |
| `source_link_escape` | Gỡ symlink/junction trỏ ra ngoài root canonical. |
| `file_limit_exceeded` | Tăng `--max-files` hoặc thu hẹp cây source. |
| `index_job_busy` | Đợi job hiện tại tới trạng thái terminal rồi index lại. |
| `serve_config_invalid` | Giữ `--host 127.0.0.1`, `--workers 1`, và đặt token không rỗng. |
| `401 unauthorized` | Gửi `X-RKG-Session` trùng `RKG_SESSION_TOKEN` từ Host loopback. |
| `409 no_active_snapshot` | Index tới khi publish xong, hoặc truyền `snapshot_id`. |
| `409 snapshot_active` | Activate snapshot khác rồi mới xóa. |
| `409 snapshot_in_use` / `repository_in_use` | Xóa hội thoại đang pin, đợi reader kết thúc, rồi xóa lại. |
| `409 repository_busy` | Đợi job của repository đó tới trạng thái terminal. |
| `409 conversation_conflict` | Đọc lại `revision` hiện tại và gửi đúng nội dung hoặc request id mới. |
| `410 snapshot_unavailable` | Hội thoại vẫn pin snapshot đã mất; tạo hội thoại mới trên snapshot còn sống. |
| `503 llm_disabled` | Đặt key của provider đã chọn (`OPENAI_API_KEY` hoặc `OPENROUTER_API_KEY`) trong `.env` rồi khởi động lại server. |
| `502` / `504 llm_timeout` | Thu câu hỏi hoặc kiểm tra provider; focus cũ vẫn còn. |

CLI in JSON có `error_code` và không in đường dẫn tuyệt đối. Log hội thoại
`rkg.conversation` chỉ có id, trạng thái và mã lỗi.

## Kiểm tra lại

```bash
uv run ruff check src tests
uv run pytest
cd frontend && npm test && npm run lint && npx tsc -b
```

Bài kiểm tra live OpenRouter được skip khi không có `OPENROUTER_API_KEY`.
Bài kiểm tra pilot dùng corpus trong `repo-test/pilot_fastapi/`. Nó skip khi
thư mục đó không có và không đặt `RKG_PILOT_REPO`. Đặt `RKG_PILOT_REPO` tới
đường dẫn không tồn tại thì bài đó fail. Kết quả regression đã ghi cho bàn giao này là
`TEST-RKG-FINAL-REGRESSION-001`.
