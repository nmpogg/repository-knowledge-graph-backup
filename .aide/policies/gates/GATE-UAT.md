---
uid:
key: GATE-UAT
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: business-owner}
relations:
  verifies: []
classification: internal
ai_assisted: true
---
# GATE-UAT — UAT Gate checklist

Checklist cho bước 18. Chỉ áp dụng change set T1/T2 có đổi FR hoặc AC.
`CHG-RKG-2026-002` đang `implementation_complete_UAT_pending`. Chưa có approval
`gate: GATE-UAT`.

- [ ] Change set view (CSV) dùng làm script được sinh từ baseline hiện tại của change set.
- [ ] Mỗi AC trong mục tính năng mới và thay đổi hành vi của CSV có `result: pass` hoặc `fail`.
- [ ] `approved_by` là người khác với `accountable_role` của FR đang nghiệm thu.
- [ ] Approval ghi `environment: staging`, `build` là commit đang chạy, và `verified_against` từng AC.
- [ ] Fail vì build lệch AC đã duyệt đi route `patch` (bug, quay lại bước 14).
- [ ] Fail vì thiếu ca thực tế đi route `intent_gap` (open question), không vá code để che khoảng trống spec.

Checklist không tạo approval và không đổi phase của change set.
