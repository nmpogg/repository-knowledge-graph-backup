---
uid:
key: CAP-RKG-003
type: capability
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 4
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {covers: [FR-RKG-005]}
classification: internal
ai_assisted: true
---
# Grounded conversation

Quản lý conversation/history/focus/repository-snapshot pin và phối hợp bounded graph retrieval với
một provider adapter để trả lời có citation hoặc yêu cầu clarification.

Ownership xuyên component: `CMP-RKG-CONVERSATION` điều phối turn/state/provider;
`CMP-RKG-GRAPH` cung cấp read-only retrieval + schema storage cho history;
`CMP-RKG-TRANSPORT` expose API Q&A; `CMP-RKG-WEB` render conversation workspace.
Không có ownership ẩn ngoài các CMP này.

