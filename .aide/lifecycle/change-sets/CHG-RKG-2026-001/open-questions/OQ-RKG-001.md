---
uid:
key: OQ-RKG-001
type: open-question
group: normative
scope: lifecycle
system: SYS-RKG
status: resolved
revision: 3
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations: {blocks: []}
classification: internal
ai_assisted: true
---
# Chọn LLM provider/model thật

**Resolved (2026-09-25):** dùng OpenRouter làm LLM provider và
`openai/gpt-4o-mini` làm model cho adapter thật tại `TASK-RKG-019`.

- Credential source: biến môi trường phía server `OPENROUTER_API_KEY`; không đưa
  credential vào browser, graph, log hay evidence.
- Tokenizer cho kiểm tra ngân sách trước request: `o200k_base` qua `tiktoken`.
  Token usage thực tế lấy từ response của OpenRouter khi có; adapter phải xử lý
  trường hợp usage vắng mặt.
- Cost metadata: dùng usage/cost do OpenRouter trả về khi có; không ghim giá tiền
  trong artifact này vì bảng giá có thể đổi. Không ghi prompt/response để tính phí.
- Giữ provider interface, timeout/token budgets theo `NFR-RKG-REL-001` và khả năng
  tắt LLM. `TASK-RKG-019` vẫn phải kiểm thử adapter và nghiệm thu live; quyết định
  này chỉ gỡ chặn việc bắt đầu task.
