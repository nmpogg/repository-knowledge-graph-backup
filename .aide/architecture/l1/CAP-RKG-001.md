---
uid:
key: CAP-RKG-001
type: capability
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 6
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {covers: [FR-RKG-001, FR-RKG-002]}
classification: internal
ai_assisted: true
---
# Repository analysis

Đăng ký source identity của repository local, chuẩn bị source bất biến, parse
mã nguồn/metadata theo language adapter, detect ngôn ngữ/framework/technology, chạy deep
extractors và tạo candidate graph/`FactBatch` có evidence/unresolved diagnostics
cùng scan report. Handoff sang `CAP-RKG-002` để validate/publish; analyzer không
ghi Kùzu. API/CLI khởi job thuộc `CMP-RKG-TRANSPORT` nhưng capability phân tích
vẫn thuộc CAP này (FR-RKG-001 chia ownership lifecycle/publication với CAP-002).
Language/framework/deep adapter tuân theo contract version hóa của `ADR-2026-005` và
registry `REG-ADAPTER-001`; core capability không phụ thuộc một adapter cụ thể.

