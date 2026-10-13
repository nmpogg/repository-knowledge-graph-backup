---
uid:
key: NFR-RKG-PERF-001
type: non-functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 5
ownership:
  accountable_team: TEAM-RKG
  accountable_role: architect
relations:
  constrains: [FR-RKG-001, FR-RKG-003, FR-RKG-004]
classification: internal
ai_assisted: true
---

# NFR-RKG-PERF-001 — Performance budgets

## Mô tả
Đặt ngân sách hiệu năng cho full scan và query graph trên máy tham chiếu. Source
manifest preparation và LLM latency đo riêng, không trộn vào chỉ số analyzer/query.

## Ngưỡng (normative)

| Metric | Điều kiện đo | Ngưỡng |
|---|---|---|
| Benchmark corpus | ≤500 source file thuộc adapter profile, ≤50.000 SLOC, graph ≤10.000 nodes / 30.000 edges | Bộ đo chuẩn pilot |
| Máy tham chiếu | ≥4 CPU cores, ≥8 GB RAM | Host đo nghiệm thu |
| Full scan wall time | Sau khi source local sẵn; không gồm LLM | ≤ 60 giây |
| Analyzer peak RAM | Trong full scan benchmark | ≤ 1 GB |
| Search/subgraph p95 | ≤200 nodes; 100 request tuần tự sau warm-up; không tính render UI | < 500 ms |
| Context API p95 | Request ở budget tối đa contract; 100 request tuần tự sau warm-up | < 500 ms |

## Ghi chú nghiệm thu
- Đây là mục tiêu đo trong pilot/M5, chưa phải SLA cho mọi repo thực tế.
- Báo cáo phải ghi cấu hình máy, commit fixture và số liệu thô — không chỉ "pass".
- `TASK-RKG-001` phải pin/ghi OS, CPU architecture, Python và Kùzu version của máy tham chiếu; thay đổi profile cần evidence mới, không sửa số đo cũ.
