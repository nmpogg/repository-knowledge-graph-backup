---
uid:
key: EPIC-004-TEAM-RKG
type: epic
group: normative
scope: lifecycle
system: SYS-RKG
status: done
revision: 6
change_set: CHG-RKG-2026-001
implements: [FR-RKG-005]
affected_components: [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
contracts: { produces: [], consumes: [API-RKG-CORE-v1, TBL-RKG-GRAPH] }
blocked_by: []
ready_criteria: [contract_frozen, context_valid, tests_green]
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {part_of: [CHG-RKG-2026-001]}
classification: internal
ai_assisted: true
---
# EPIC-004-TEAM-RKG — M4 Q&A nhiều lượt

Conversation persistence, provider integration và grounded multi-turn Q&A.

## Phạm vi

Một team. Giao lưu hội thoại, trả lời bám snapshot đã pin, rồi API và UI. Provider tắt không được làm hỏng search.

## Story

- STORY-RKG-012 — Lưu conversation và pin snapshot
- STORY-RKG-013 — Provider LLM và câu trả lời grounded có lịch sử
- STORY-RKG-014 — API và UI hội thoại

## Done when

`TASK-RKG-018..021` hoàn tất; Q&A, history, security, retention, recovery và a11y
đạt AC-RKG-024/025/028..033/041/042/044..047/059/063/064 với provider thật ở live eval.
