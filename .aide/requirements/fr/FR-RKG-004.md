---
uid:
key: FR-RKG-004
type: functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 6
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  satisfies: [GOAL-RKG-002]
  constrained_by: [NFR-RKG-PERF-001, NFR-RKG-REL-001, NFR-RKG-SEC-001]
classification: internal
ai_assisted: true
---

# FR-RKG-004 — Trích xuất bounded context

## Mô tả

Hệ thống xuất context JSON theo repository, snapshot và root entity, gồm entities, relationships, evidence, diagnostic summary, budget và trạng thái truncation. Output deterministic, chỉ đọc graph đã publish, không trả raw source hoặc secret và không cần LLM để hình thành context.

## Acceptance Criteria

### Context extraction

#### AC-RKG-010
- **given** cùng snapshot_id và cùng request context hợp lệ
- **when** gọi POST /api/v1/context nhiều lần
- **then** schema và thứ tự deterministic; budget depth/nodes/edges/chars được tôn trọng; truncated và truncation_reasons phản ánh đúng khi còn dữ liệu ngoài phần trả; response không chứa raw source, secret/config value hoặc nội dung do LLM sinh
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-GRAPH, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-CONTEXT]

#### AC-RKG-062
- **given** benchmark corpus/máy tham chiếu và context request ở ngân sách tối đa theo API contract
- **when** chạy workload `POST /api/v1/context` tuần tự sau warm-up
- **then** báo cáo số liệu thô, cấu hình máy và p95 đạt hoặc không đạt ngưỡng context của NFR-RKG-PERF-001
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-CONTEXT-BENCHMARK]
