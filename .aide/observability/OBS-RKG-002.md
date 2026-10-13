---
uid:
key: OBS-RKG-002
type: observability-spec
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 4
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  measures: [KPI-RKG-002]
  constrained_by: []
classification: internal
ai_assisted: true
---
# OBS-RKG-002 — Pilot edge precision

## Mục tiêu đo
Precision theo nhóm edge đã rà soát trên pilot repository.

## Cách đo
- Chốt pilot repository, manifest/snapshot và taxonomy nhóm edge trước khi review.
- Với population nhỏ hơn ngưỡng, review toàn bộ. Với population lớn hơn, lấy mẫu
  deterministic từ danh sách edge sort theo stable ID bằng seed được ghi trong report.
- Rà soát tối thiểu 30 mẫu cho nhóm import/call/DI và tối thiểu 10 mẫu cho từng nhóm DB/event/config/implements nếu pilot có đủ dữ liệu (OQ-RKG-002).
- Reviewer mở evidence và source context để gán từng edge là `TP` hoặc `FP`; bất đồng
  được Product Owner/Tech Lead adjudicate và giữ cả quyết định ban đầu lẫn kết luận.
- Precision nhóm `g` = `TP_g / (TP_g + FP_g)`. Báo cáo population, sample size,
  TP, FP, unresolved và omissions theo từng nhóm.
- Nhóm không xuất hiện ghi `N/A`; nhóm có population nhưng không đạt minimum sample
  ghi `insufficient_sample`. Không hạ denominator hoặc gộp nhóm để che thiếu mẫu.
- Target MVP: **≥95% / nhóm được công bố**.

## Nguồn dữ liệu
Pilot review sheet có stable edge IDs/seed/labels + pinned graph snapshot
(`CMP-RKG-GRAPH`) + adjudication log.

## Owner nghiệm thu
Product Owner + Tech Lead (TEAM-RKG).
