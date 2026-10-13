---
uid:
key: GATE-PRODUCTION
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: sre}
relations:
  verifies: []
classification: internal
ai_assisted: true
---
# GATE-PRODUCTION — Production Gate checklist

Checklist cho bước 20. Áp dụng mọi release. Approval record, nếu có, nằm ở
`evidence/approvals/` và trỏ `gate: GATE-PRODUCTION`. Checklist này không tạo
approval và không đổi phase của change set.

- [ ] Release plan có thứ tự unit (`order`) và ranh giới rollback cho từng unit.
- [ ] Unit không rollback được đã khai `rollback` khác `reversible`, kèm lý do.
- [ ] Evidence của lát release đủ cho baseline đang đưa ra gate. `not_run` không tính là `passed`.
- [ ] Approval có `commit_sha` của cây đang release.
- [ ] Approval có `human_presence` với bằng chứng người thật.
- [ ] `accepted_risk` liệt kê mọi finding còn mở. Mục rỗng chỉ khi không còn finding mở.
- [ ] `rejected_findings` khai tường minh từng finding bị bác, kèm lý do khác rỗng.
- [ ] `approved_by` là danh tính người được ủy quyền, không phải nhãn role.

## Change Integration Gate

Một team và `coordination.mode: independent` thì Change Integration Gate cố ý
không áp dụng. Production Gate không thay cho Change Integration Gate.
