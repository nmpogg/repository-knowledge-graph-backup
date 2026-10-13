---
uid: null
key: TASK-RKG-000
type: task
group: normative
scope: lifecycle
system: SYS-RKG
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 5
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - CHG-RKG-2026-001
  implements:
  - PRD-RKG
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-000.yaml
  plan: PLAN-TASK-RKG-000.md
  diary: DIARY-TASK-RKG-000.md
---
# TASK-RKG-000 — Chuyển bộ docs hiện có sang artifact docs-first

## Làm gì

Tạo PRD, FR/AC, NFR, domain glossary, L1/L2, ADR, threat model, API/schema,
UX/UI, registry, Change Set và backlog artifact; không triển khai source code.

## Vị trí trong workflow

Task này là bước dựng artifact gốc của flow New System (PRD, FR/AC, domain, L1/L2, contract, UX/UI, Change Set), trước khi bước 11 tách Epic và Story. Không có AC người dùng để `satisfies`, nên không tạo Story và không treo lên một Epic. Cha điều phối là `CHG-RKG-2026-001`.

## Xong khi

- Artifact có frontmatter, đúng vị trí và quan hệ truy vết cơ bản.
- Năm capability FR-RKG-001…005, toàn bộ AC hiện hành và các task có artifact tương ứng.
- Gate và câu hỏi chưa quyết định được ghi đúng trạng thái, không giả approval.
- Kiểm tra cấu trúc, key reference và YAML đã chạy; evidence được ghi.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-000.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-000.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-000.md) — kết quả, evidence và các correction.
