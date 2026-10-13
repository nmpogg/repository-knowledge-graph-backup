---
uid:
key: OBS-RKG-001
type: observability-spec
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  measures: [KPI-RKG-001]
  constrained_by: []
classification: internal
ai_assisted: true
---
# OBS-RKG-001 — Fixture extraction gate

## Mục tiêu đo
Tỷ lệ expected facts khớp trên fixture pattern được hỗ trợ (đơn vị: fact đã gán nhãn).

## Cách đo
- Pin fixture revision, analyzer/schema/adapter versions và scan config; chạy toàn bộ
  fixture của supported patterns, không lấy mẫu.
- Canonicalize actual và expected facts: bỏ generated ID/timestamp, sort theo semantic
  identity; giữ type, qualified identity, attributes bắt buộc, relationship direction,
  `rule_id` và relative evidence location trong phép so sánh.
- `TP`: actual fact khớp đúng một expected fact; `FN`: expected fact bị thiếu; `FP`:
  actual fact không có expected tương ứng và không nằm trong explicit allowlist đã duyệt.
- Tính `coverage = TP / (TP + FN)` và `precision = TP / (TP + FP)` cho toàn bộ corpus,
  đồng thời báo cáo riêng theo entity/edge type và từng fixture.
- Target MVP (M5): coverage = **100%**, precision = **100%**, không fixture bắt buộc nào fail.

## Nguồn dữ liệu
Expected JSON đã review + raw/canonical diff + test harness report của analyzer
(`CMP-RKG-ANALYZER`). Không lấy từ LLM.

## Owner nghiệm thu
Tech Lead (TEAM-RKG).
