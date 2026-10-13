---
uid:
key: UXF-RKG-003
type: ux-flow
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 6
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations: {satisfies: [FR-RKG-001]}
classification: internal
ai_assisted: true
---
# UXF-RKG-003 — Repository and snapshot management flow

## Mục tiêu và mental model

Repository là đăng ký bền vững của một source local; index/re-index tạo snapshot mới
bất biến; activate chỉ đổi con trỏ active. UI phải giữ ba khái niệm này tách biệt để
người dùng không hiểu nhầm edit repository sẽ sửa snapshot cũ.

## Luồng chính

1. Người dùng mở **Repositories** và thấy nav active, danh sách repository, active snapshot cùng
   trạng thái loading/empty/error; empty state có CTA tạo repository.
2. Create nhập local path và defaults. Thành công mở repository
   detail; không tự index. Duplicate/validation error giữ input và focus.
3. Detail cho phép sửa display name/source root/app/scan defaults bằng
   optimistic revision. Source type/path chỉ đọc; muốn đổi source phải tạo repo mới.
4. Người dùng start index và theo dõi Job. Thành công thêm snapshot mới, đặt active
   và có CTA mở Explorer; thất bại giữ active snapshot trước.
5. Snapshot list newest-first cho phép xem metadata, activate snapshot retained hoặc
   xóa snapshot không active/không referenced. Activate không tạo job.
6. Snapshot delete bị guard giữ nguyên list/selection và giải thích active/in-use;
   successful delete đưa focus về heading/list item kế tiếp và announce kết quả.
7. Repository delete dùng confirm nêu phạm vi cascade. Busy/in-use giữ repository;
   thành công quay về list và announce kết quả.
8. Explorer/Q&A luôn hiện repository + snapshot đang dùng; conversation cũ tiếp tục
   dùng pin cũ khi active snapshot thay đổi.

## Recovery branches

- `409 repository_conflict`: reload server state, giữ draft để người dùng review/retry.
- `409 index_job_busy`: hiển thị job đang chạy; không submit job thứ hai.
- `409 snapshot_active|snapshot_in_use`: không xóa; đưa link tới active state hoặc
  conversation liên quan khi contract cho phép mà không lộ nội dung.
- `409 repository_busy|repository_in_use`: không cascade một phần; nêu bước giải phóng.
- `410 snapshot_unavailable`: Explorer/citation có recovery về repository detail và
  re-index; lifecycle list không coi payload đã mất là snapshot khả dụng.
- Ownership mismatch/not found: response chung, không hiển thị metadata repository khác.
- Dialog keyboard/focus/live-region behavior tuân theo `NFR-RKG-UX-001`.

## Copy bắt buộc cho hành động rủi ro

- **Re-index:** “Tạo snapshot mới; snapshot đang active chỉ đổi khi publish thành công.”
- **Activate:** “Đổi snapshot mặc định cho Explorer/conversation mới; conversation
  hiện có vẫn dùng snapshot đã pin.”
- **Delete snapshot:** nêu snapshot ID rút gọn, created time và dữ liệu graph/evidence
  sẽ bị xóa; không hứa xóa nếu active/in-use.
- **Delete repository:** nêu rõ cascade repository, job và snapshot con đủ điều kiện;
  không hiển thị absolute path.

## Focus và continuity

- Validation/conflict đưa focus đến summary rồi liên kết tới field lỗi đầu tiên.
- Confirm dialog trả focus về trigger khi cancel/blocked; sau delete success, focus tới
  heading hoặc item kế cận ổn định.
- Refresh/retry giữ search, paging và unsaved draft khi có thể; không giữ session token
  trong persisted browser storage.
