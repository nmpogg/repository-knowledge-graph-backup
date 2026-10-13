---
uid:
key: GATE-MERGE
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  verifies: []
classification: internal
ai_assisted: true
---
# GATE-MERGE — Component Merge Gate checklist

Checklist cho bước 16. Approval record trỏ `gate: GATE-MERGE`. Checklist không
tự đổi trạng thái change set.

- [ ] Structural, referential và scope check của lát cắt đang merge là `passed` hoặc finding được ghi tường minh. `not_run` không tính là `passed`.
- [ ] Review class `adversarial` đã có receipt. Trần hai vòng. Vòng sau giữ nguyên ID finding.
- [ ] Test của lát cắt xanh trên cây đang xét, có attribution về baseline của change set.
- [ ] Context snapshot của task còn khớp artifact revision đang merge.
- [ ] MR hoặc change set khai đủ quan hệ tới story/task, AC và component bị chạm.
- [ ] Tech Lead ký approval append-only, đúng phạm vi lát cắt. Một approval không đóng gate của change set khác.

## Phạm vi đã ghi

`approval-012` và `approval-013` là quyết định người đã ký cho các lát
`TASK-RKG-030` và `TASK-RKG-031`…`035` trên `CHG-RKG-2026-002`. Chúng không đóng
Component Merge Gate của `CHG-RKG-2026-001` hay của `CHG-RKG-2026-003`…`014`.
Các change set đó vẫn `component_merge: pending` trong `change-set.yaml`.
