---
uid:
key: UXF-RKG-001
type: ux-flow
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 7
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations: {satisfies: [FR-RKG-001, FR-RKG-002, FR-RKG-003, FR-RKG-004]}
classification: internal
ai_assisted: true
---
# UXF-RKG-001 — Onboarding to evidence flow

## Mục tiêu và điều kiện

Đưa người dùng từ một thư mục local hợp lệ đến một graph có evidence mà không yêu
cầu LLM. Luồng bắt đầu khi dịch vụ local sẵn sàng và kết thúc khi người dùng đã mở
evidence hoặc tải context JSON từ một snapshot được publish.

UI luôn hiển thị repository/snapshot identity hiện tại; dữ liệu source locator chỉ
được hiển thị ở dạng đã redact.

## Luồng chính

1. Người dùng mở Repository, tạo source từ thư mục local hoặc chọn repository đã có.
2. Khi tạo mới, hệ thống validate local path và đăng ký repository nhưng chưa index.
3. Người dùng bắt đầu index repository; nếu có nhiều application entrypoint candidate thì yêu cầu chọn app;
   technology/adapter detections hiển thị như capability và không chặn publish.
4. Người dùng theo dõi queued/detecting/indexing.
5. `succeeded` mở active snapshot của repository; `succeeded_with_warnings` hiển thị warning/report
   trước khi tiếp tục; `failed` không thay active snapshot cũ.
6. Người dùng search theo symbol hoặc method/path và chọn một entity.
7. Explorer hiển thị một hop; người dùng filter/expand hoặc dùng preset API→DB,
   Event participants, Config users, Interface implementations.
8. Chọn node/edge mở evidence và copy `relative_path:line`.
9. Người dùng export context JSON của root hiện tại.

## Nhánh phụ

Từ Explorer, người dùng bấm Structure để đọc cây của cả snapshot, chọn một lá để
mở evidence, rồi có thể bấm Graph hoặc List để về chế độ cũ. Nhánh này không phải
bước bắt buộc của luồng search, graph, preset hay export context.

## Trạng thái và điểm quyết định

| Điểm | Trạng thái bắt buộc | Hành động tiếp theo |
|---|---|---|
| Repository catalog | loading, empty, ready, error | Create hoặc open repository |
| Create repository | initial, validating, submitting, invalid, saved | Sửa input hoặc mở detail |
| Index job | queued, detecting, indexing | Chờ theo `Retry-After`; cho rời màn hình an toàn |
| App selection | multiple candidates | Chọn explicit candidate; không auto-select |
| Scan result | succeeded, succeeded_with_warnings, failed | Mở snapshot/report hoặc retry |
| Entity search | loading, empty, ready, error | Đổi query/filter hoặc chọn entity |
| Subgraph | loading, ready, truncated, stale/unavailable | Điều chỉnh budget hoặc recovery |
| Evidence/context | loading, ready, unavailable/error | Copy locator, retry hoặc quay về detail |

## Recovery branches

- Repository validation failure: giữ input, nêu lỗi mà không tạo repository một phần.
- Index failure: giữ repository/defaults, cho retry, không mất active snapshot cũ.
- Empty result: nói “không tìm thấy trong snapshot này”, gợi ý filter/query khác.
- Truncated graph: hiển thị badge và budget control; không gọi là toàn bộ dependency.
- LLM disabled: chat disabled có giải thích; search/explorer vẫn hoạt động.
- `401` local session/origin failure: dừng mutation, không lặp tự động và hướng dẫn
  reload dịch vụ local; không hiển thị token.
- `409 index_job_busy`: mở job đang chạy nếu có định danh; không tạo job thứ hai.
- `410 snapshot_unavailable`: giữ repository context, vô hiệu action cần payload và
  đưa CTA về repository detail để re-index.

## Tiêu chí thoát

- Success: người dùng mở được entity/evidence từ đúng snapshot và context export
  công bố budget/truncation.
- Recoverable stop: repository/defaults và active snapshot trước vẫn còn nguyên.
- Không được coi blank canvas, graph rỗng giả hoặc auto-selected candidate là success.
