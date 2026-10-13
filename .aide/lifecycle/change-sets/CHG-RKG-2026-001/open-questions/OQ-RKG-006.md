---
uid:
key: OQ-RKG-006
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: open
revision: 4
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

Câu hỏi còn mở. Chưa có signer identity được tổ chức ủy quyền.

`GATE-RKG-SCOPE`, `GATE-RKG-ARCHITECTURE`, `GATE-RKG-UIUX` và
`GATE-RKG-CONTRACT` đang `pending` trên Change Set. PRD revision hiện tại chưa
được Scope Gate ký lại. Candidate baseline hiện hành là
`BL-CHG-RKG-2026-001` revision 3 (`status: candidate`), chưa phải approval.
Tên lịch sử `BL-r1` / `BL-r2` chỉ còn trong `revision_history` và evidence cũ;
không còn file baseline riêng.

`approval-004` chỉ khóa `PRD-RKG` revision 16 và các revision FR/NFR ghi trong
record đó. Record cố ý để trống `approvers`. Nó không đóng Scope Gate cho
revision hiện tại và không đóng UI/UX Gate.

OQ này chặn approval mới của Scope Gate và UI/UX Gate cho candidate baseline.
Nó không tự đổi `status` của artifact và không được ghi là đã resolve.

## Lịch sử revision 2

Revision 2 ghi rằng Scope Gate đã đóng theo `approval-004`. Câu đó không còn
đúng với gate hiện tại. Nội dung đó được giữ làm lịch sử, không phải trạng thái
hiện tại.

## Điều kiện resolve

Một approval record mới cho exact revision hiện tại chứa signer identity hợp lệ
cho mọi role bắt buộc của gate đang ký. Không dùng role label làm `name`.
Không gán quyết định cho tooling. Resolve record này không thay cho việc ký gate.
