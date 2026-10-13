---
uid:
key: OQ-RKG-006
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 5
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations:
  part_of: [CHG-RKG-2026-001]
  blocks: [GATE-RKG-SCOPE, GATE-RKG-UIUX]
classification: internal
ai_assisted: true
---
# Danh tính người ký candidate baseline

## Câu hỏi

Ai là người hoặc signer identity được tổ chức ủy quyền để ký UI/UX Gate (và
backfill identity cho Scope nếu tổ chức yêu cầu) cho revision hiện tại?

## Trạng thái hiện tại

Đã resolve ở revision 5. Người được ủy quyền ghi trong `approval-014` là PhongNM.
Quyết định ngày 2026-10-13. Bản ghi này không đổi `approval-004`.

`approval-004` vẫn chỉ khóa `PRD-RKG` revision 16 và cố ý để trống `approvers`.
Chữ ký hiện tại là `approval-014`, không phải `approval-004`.

## Lịch sử revision 4

Revision 4 còn ghi gate đang pending và OQ còn chặn chữ ký mới. Câu đó đúng tới
trước `approval-014`. Giữ làm lịch sử.

## Lịch sử revision 2

Revision 2 ghi rằng Scope Gate đã đóng theo `approval-004`. Câu đó không còn
đúng với gate hiện tại. Nội dung đó được giữ làm lịch sử, không phải trạng thái
hiện tại.

## Điều kiện resolve

Một approval record mới cho exact revision hiện tại chứa signer identity hợp lệ
cho mọi role bắt buộc của gate đang ký. Không dùng role label làm `name`.
Không gán quyết định cho tooling. Resolve record này không thay cho việc ký gate.
