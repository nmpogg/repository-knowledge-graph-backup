---
key: EPIC-006-TEAM-RKG
group: normative
scope: lifecycle
system: SYS-RKG
revision: 2
change_set: CHG-RKG-2026-002
classification: internal
ai_assisted: true
type: epic
status: in_progress
implements:
- FR-RKG-005
affected_components:
- CMP-RKG-GRAPH
- CMP-RKG-CONVERSATION
- CMP-RKG-TRANSPORT
- CMP-RKG-WEB
contracts:
  produces: []
  consumes:
  - API-RKG-CORE-v1
  - TBL-RKG-GRAPH
  - UIS-RKG-001
  - CON-RKG-CONVERSATION-v1
blocked_by: []
ready_criteria:
- contract_frozen
- context_valid
- tests_green
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  part_of:
  - CHG-RKG-2026-002
---
# EPIC-006-TEAM-RKG — Chatbot dễ hỏi và trả lời tự nhiên

Triển khai delta đã duyệt trong baseline r8. Một TEAM-RKG, thực hiện tuần tự theo dependency; không có dependency team ngoài. User đã yêu cầu bắt đầu tại CR-RKG-010; thứ tự kỹ thuật do agent đề xuất từ dependency đã duyệt.

## Story

- STORY-RKG-020 — Lưu bền câu hỏi gốc và thông tin câu trả lời
- STORY-RKG-021 — Hiểu câu hỏi và trả lời quan hệ có bằng chứng
- STORY-RKG-022 — Contract HTTP và nguồn của đúng lượt
- STORY-RKG-023 — Ask dễ đọc và kiểm chứng toàn luồng

## Story theo change set sau baseline r8

Mỗi lát cắt có AC riêng, task đã `done` và evidence current-tree. Story giữ `in_progress` đến khi Component Merge Gate của change set được quyết định.

- STORY-RKG-030 — Bỏ trần budget ứng dụng cho chatbot (`CHG-RKG-2026-003`)
- STORY-RKG-031 — Chọn provider OpenAI trực tiếp (`CHG-RKG-2026-004`)
- STORY-RKG-032 — Chẩn đoán lượt hỏng và làm rõ câu trả lời thất bại (`CHG-RKG-2026-005`)
- STORY-RKG-033 — Debug chatbot chi tiết trên terminal (`CHG-RKG-2026-006`)
- STORY-RKG-034 — Đường dẫn narrative graph hợp lệ (`CHG-RKG-2026-007`)
- STORY-RKG-035 — Câu hỏi thực thể và vị trí nguồn tự nhiên (`CHG-RKG-2026-008`)

## Hoàn tất

Story 020–023: task có current-tree evidence và AC verification; UAT người dùng còn pending. Story 030–035: implementation đã review độc lập, gate còn pending. Không suy release readiness từ Contract approval hay từ task `done`.
