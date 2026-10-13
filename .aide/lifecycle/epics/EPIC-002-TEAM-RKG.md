---
uid:
key: EPIC-002-TEAM-RKG
type: epic
group: normative
scope: lifecycle
system: SYS-RKG
status: draft
revision: 15
change_set: CHG-RKG-2026-001
implements: [FR-RKG-001, FR-RKG-002, FR-RKG-004]
affected_components: [CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT]
contracts: { produces: [API-RKG-CORE-v1, TBL-RKG-GRAPH], consumes: [] }
blocked_by: []
ready_criteria: [contract_frozen, context_valid, tests_green]
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {part_of: [CHG-RKG-2026-001]}
classification: internal
ai_assisted: true
---
# EPIC-002-TEAM-RKG — M1/M2 Analyzer, graph store và API

Repository catalog, source ingestion, domain schema, static extraction, Kùzu
snapshot/query/lifecycle và API v1.

## Phạm vi

Một team. Giao pipeline phân tích, publication, đọc graph và HTTP v1. UI mock chạy song song ở EPIC-001, không chặn epic này.

## Story

- STORY-RKG-003 — Nạp source local mà không thực thi
- STORY-RKG-004 — Cấu trúc Python, import, lời gọi và quan hệ class
- STORY-RKG-005 — Inventory dependency và chọn adapter
- STORY-RKG-006 — Trích xuất FastAPI, SQLAlchemy, messaging và config
- STORY-RKG-007 — Publish snapshot Kùzu nguyên tử
- STORY-RKG-008 — Tìm kiếm, duyệt graph và bounded context
- STORY-RKG-009 — Điều phối index job và CLI
- STORY-RKG-010 — API repository, job, graph và session
- STORY-RKG-017 — Directory thay Namespace trên snapshot mới
- STORY-RKG-018 — Bao phủ static FastAPI còn thiếu

## Story theo change set adapter

Mỗi story một change set. CR và phần loại trừ của story không ghi một lát release chung. Story và task giữ `in_progress`, phase `verified_deep_support_withheld`. Chưa có REV-TASK. Không thăng deep-supported. Epic giữ `draft`.

- STORY-RKG-026 — TypeScript language + React Router framework extraction (`CHG-RKG-2026-009`)
- STORY-RKG-027 — Vue language + Nuxt framework extraction (`CHG-RKG-2026-010`)
- STORY-RKG-028 — BullMQ messaging extraction (`CHG-RKG-2026-011`)
- STORY-RKG-029 — Java + Spring + JPA + Spring Kafka extraction (`CHG-RKG-2026-012`)
- STORY-RKG-024 — Go + kafka-go + pgx extraction (`CHG-RKG-2026-013`)
- STORY-RKG-025 — Flask static route extraction (`CHG-RKG-2026-014`)

## Task (không qua Story — không có AC)

- TASK-RKG-002 — Domain schema and golden fixtures
- TASK-RKG-004 — Analyzer adapter contract and conformance suite

## Done when

`TASK-RKG-002..016`, `TASK-RKG-027`, `TASK-RKG-028`, `TASK-RKG-042`,
`TASK-RKG-043`, `TASK-RKG-044`, `TASK-RKG-045`, `TASK-RKG-046` và `TASK-RKG-047` hoàn tất; extraction/negative
fixtures, atomic publication, single-writer, search/traversal/context,
repository/snapshot lifecycle, CLI và API security AC liên quan — gồm
AC-RKG-048..055/058/060/062/065…072 — Directory/Namespace và phần static
FastAPI của STORY-RKG-017/018, TypeScript/React Router của STORY-RKG-026,
Vue/Nuxt của STORY-RKG-027, BullMQ của STORY-RKG-028, Java/Spring/JPA/Spring
Kafka của STORY-RKG-029, Go + kafka-go + pgx của STORY-RKG-024, Flask static route của STORY-RKG-025, cùng adapter conformance của NFR-RKG-EXT-001 đều có
test evidence. `TASK-RKG-042..047` hiện vẫn `in_progress` trên CHG-RKG-2026-009…014. Epic giữ `draft` cho đến khi gate được ký lại; trạng thái task
`done` không đóng epic.
