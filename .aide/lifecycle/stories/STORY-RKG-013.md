---
uid:
key: STORY-RKG-013
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-004-TEAM-RKG
status: done
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-004-TEAM-RKG]
satisfies: [AC-RKG-024, AC-RKG-025, AC-RKG-028, AC-RKG-029, AC-RKG-032, AC-RKG-042, AC-RKG-063, AC-RKG-064]
classification: internal
ai_assisted: true
---
# STORY-RKG-013 — Provider LLM và câu trả lời grounded có lịch sử

## Giao cái gì

Provider interface (OpenRouter là adapter đầu) và lớp trả lời: câu hỏi Việt/Anh bám context của snapshot đã pin, citation thuộc context, follow-up giữ focus, ambiguity thì clarification. Provider tắt, timeout hoặc output hỏng không bịa fact và không làm hỏng search. Injection không chạy tool ngoài allowlist. Nội dung lưu đã redact. `AC-RKG-032` được `TASK-RKG-020` kiểm: hỏi tiếp khi vượt window thì bỏ turn cũ, giữ state, trả `context_turn_ids` và `history_truncated`. Persistence của conversation vẫn thuộc STORY-RKG-012.

## Ngoài phạm vi

Route HTTP và màn hình thuộc STORY-RKG-014. Eval trên corpus pilot thuộc STORY-RKG-015.

## Task

- TASK-RKG-019 — LLM provider interface and adapter
- TASK-RKG-020 — History-aware grounded Q&A
