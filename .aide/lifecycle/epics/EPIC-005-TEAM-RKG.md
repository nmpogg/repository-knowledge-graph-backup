---
uid:
key: EPIC-005-TEAM-RKG
type: epic
group: normative
scope: lifecycle
system: SYS-RKG
status: done
revision: 8
change_set: CHG-RKG-2026-001
implements: [FR-RKG-001, FR-RKG-003, FR-RKG-004]
affected_components: [CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-CONVERSATION]
contracts: { produces: [], consumes: [API-RKG-CORE-v1, TBL-RKG-GRAPH] }
blocked_by: []
ready_criteria: [contract_frozen, context_valid, tests_green]
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations: {part_of: [CHG-RKG-2026-001]}
classification: internal
ai_assisted: true
---
# EPIC-005-TEAM-RKG — M5 Pilot và bàn giao

Đo extraction/Q&A/performance trên fixture và pilot, sửa finding, hoàn thiện runbook.

## Phạm vi

Một team. Công bố số đo và finding. Không dùng kết quả đo để tự đóng gate.

## Story

- STORY-RKG-015 — Đo extraction, Q&A và hiệu năng trên pilot

## Task (không qua Story — không có AC)

- TASK-RKG-023 — Final runbook and handoff

## Done when

`TASK-RKG-022/023` hoàn tất; OBS-RKG-001, OBS-RKG-002 và OBS-RKG-005 có raw
evidence, sample/method/version; performance và adapter extensibility được nghiệm
thu qua NFR tương ứng; mọi blocking finding được đóng và release readiness được
con người phê duyệt.

`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001` ghi KPI-RKG-001 coverage 1.00 và precision
1.00, chưa có oracle review receipt. `TEST-RKG-PILOT-REVIEW-SUMMARY-002` và
`TEST-RKG-PERF-SUMMARY-002` ghi precision pilot và lần benchmark số ngày
2026-10-08. Status epic khớp `TASK-RKG-022` và `TASK-RKG-023` đã `done`. Các
biên bản đo không ký gate. Benchmark nằm dưới trần 500 file / 50.000 SLOC.
