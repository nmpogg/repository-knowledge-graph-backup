---
uid:
key: OQ-RKG-002
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 6
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {blocks: [], resolved_by: [TEST-RKG-PILOT-CORPUS-001, TEST-RKG-PILOT-CORPUS-002]}
classification: internal
ai_assisted: true
---
# OQ-RKG-002 — Chọn pilot repository

**Expected resolution:** trước khi bắt đầu `TASK-RKG-022`.

Team cần chọn một FastAPI repository nhỏ đại diện cho pattern hỗ trợ, có quyền rà
soát và đủ dữ liệu để thẩm định tối thiểu 30 mẫu import/call/DI và 10 mẫu cho từng
nhóm DB/event/config/implements nếu có đủ dữ liệu. Nhóm không xuất hiện ghi `N/A`
và vẫn phải đạt fixture riêng. Quyết định phải được ghi trước khi bắt đầu
`TASK-RKG-022`; không chặn implementation nhưng chặn pilot và báo cáo nghiệm thu.

**Resolved 2026-09-28:** chọn `../pilot_fastapi/` phiên bản 0.1.0, cùng cấp với
root RKG theo yêu cầu của operator. Repository này do nhóm tạo tại chỗ nên có toàn quyền
đọc và rà soát. Kiểm tra tĩnh hiện tại đếm được 36 import, 48 call, 48 DI,
và ít nhất 12 cạnh cho từng nhóm DB/event/config/implements; số liệu, phương
pháp và digest của source được ghi ở `TEST-RKG-PILOT-CORPUS-001`. Đây là pilot
synthetic có cấu trúc lặp lại; Task 22 phải công bố hạn chế này và tự chấm mẫu,
không suy ra precision từ số lượng cạnh ứng viên. Bản ghi
`TEST-RKG-PILOT-CORPUS-001` phản ánh vị trí ban đầu bên trong RKG;
`TEST-RKG-PILOT-CORPUS-002` xác nhận vị trí cùng cấp và digest không đổi.
