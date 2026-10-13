---
key: PLAN-CHG-RKG-2026-002-r2
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: 2026-10-06
change_set: CHG-RKG-2026-002
stage: selected-requirement-and-design-content
non_normative: true
implementation_ready: false
captured_against:
  code_commit: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  context: CTX-CHG-RKG-2026-002-r2
  candidate_baseline: BL-CHG-RKG-2026-002-r1
  authorization: CR-RKG-003
previous_plan: PLAN-CHG-RKG-2026-002
classification: internal
ai_assisted: true
---
# PLAN-CHG-RKG-2026-002-r2 — Selected scope and design handoff

## Quyết định đã ghi nhận

FR-RKG-005 revision 8 thêm AC-RKG-074…081, giữ nguyên AC cũ. ADR-2026-007
chọn B: model chọn cấu trúc dẫn giải bằng edge/path references; backend kiểm
tra topology/direction/evidence và dựng lời giải thích. Không cho model publish
free-form factual answer. A chỉ là fallback trên facts đã kiểm chứng, không
hợp thức hóa malformed/foreign output và không gọi thêm model.

Ngôn ngữ gồm Việt không dấu; tín hiệu ngôn ngữ không rõ dùng UI locale, thiếu
locale dùng vi. Endpoint resolve theo method/path và loại Endpoint. Clarification
giữ ý định gốc, greeting không đổi focus/pending và không tạo query/model call.
Answer tách direct/indirect, không suy diễn body/semantics từ tên. UI hiển thị một
answer, nguồn có nhãn, chi tiết thu gọn, insufficient không lặp, limitations bền
sau reload và metadata legacy unknown. Evidence phải đúng citation ID.

## Phạm vi thực hiện ở lượt chốt

Draft requirements, ADR/L2, UX cấp 1–3 và threat controls được hoàn thiện thành
nội dung selected để review. Candidate baseline/context mới pin hash của các bản
này; gate checklists giữ pending. Không sửa plan/context khảo sát cũ, approval
lịch sử hoặc runtime. Không tự ký hoặc gán user một signer identity.

Đây là chuẩn bị nội dung, không tuyên bố đã vượt Scope/Architecture/UIUX Gate.
UI mock, independent advisory review và human gate signatures còn not_run/not_recorded.
Author structural verification không phải independent review.

## Công việc tiếp theo theo thứ tự workflow

1. Scope review exact FR revision/hash từ CSV được sinh từ candidate baseline;
   nếu sửa lại nội dung sau review, bump revision và lập evidence mới.
2. Sau Scope Gate, Architecture advisory review và UX token-based prototype với
   walkthrough thật; dùng normative package, không đưa plan/diary/rationale tác giả
   vào reviewer package. UI/UX Gate ký UXF/SCR/UID, không ký mock.
3. Sau prerequisite gates, draft L3/UIS: locale semantic equality, metadata persist,
   pending intent và exact evidence binding. Đánh giá JSON-column fit trước DDL;
   nếu cần migration, sửa TBL/extract và execute theo quy tắc Contract Gate.
4. Chốt contract compatibility rồi decomposition/context/task implementation plans.
   Không tạo task sớm hoặc mở lại TASK-020/021 đã done để chứa AC mới.
5. RED/GREEN, automated checks, review độc lập, UAT, release tiếp tục theo plan r1.

Chưa gọi live provider, chưa chạy runtime tests hoặc browser/UAT ở lượt này.
Tài liệu L3/TBL/UIS hiện hành được pin để đối chiếu, không bị sửa trước gate.
Generator review views là tooling tài liệu, không phải implementation chatbot.
