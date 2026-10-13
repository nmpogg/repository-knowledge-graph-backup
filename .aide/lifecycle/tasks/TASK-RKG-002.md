---
uid: null
key: TASK-RKG-002
type: task
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-001
  implements:
  - FR-RKG-002
  - FR-RKG-004
  - FR-RKG-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-002.yaml
  plan: PLAN-TASK-RKG-002.md
  diary: DIARY-TASK-RKG-002.md
---
# TASK-RKG-002 — Domain schema and golden fixtures

Định nghĩa entity/edge/evidence/diagnostic/config/IDs và golden schema fixtures.
Task này treo thẳng epic, không có `satisfies`. Nó không sở hữu AC của story khác.

Schema-level fixture trong diary kiểm shape mà các story sau `satisfies`.
Current ownership: `AC-RKG-002` thuộc `STORY-RKG-017`; `AC-RKG-007` vẫn được
`STORY-RKG-004` và `STORY-RKG-017` cùng liệt kê; `AC-RKG-010` thuộc
`STORY-RKG-008`. Revision 5 từng ghi `AC-RKG-002` thuộc `STORY-RKG-004`. Diary
ghi đó là check schema/DTO, chưa phải nghiệm thu product AC.

## Kết quả

Canonical DTO, ID helpers, candidate graph validator, context DTO/serializer và
golden source-structure fixture đã có trong `src/rkg/domain/` và `tests/`.
Schema-level checks nêu trên, toàn bộ pytest và Ruff đã pass trên cây mã được
ghi hash trong `DIARY-TASK-RKG-002`. Scan, publication và bounded traversal/API
end-to-end vẫn thuộc các task phụ thuộc sau.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-002.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-002.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-002.md) — kết quả, evidence và các correction.
