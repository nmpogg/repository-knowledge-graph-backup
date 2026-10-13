---
uid:
key: STORY-RKG-018
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: done
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-005, AC-RKG-020, AC-RKG-040, AC-RKG-052]
classification: internal
ai_assisted: true
---
# STORY-RKG-018 — Bao phủ static FastAPI còn thiếu

## Giao cái gì

Bốn chỉnh đã được xác nhận: extract FastAPI khi version chưa biết nhưng giữ `version_unverified`; factory cục bộ không tham số và một nhánh return; vòng lặp router trên list/tuple literal, không chạy Python; path rỗng kế thừa prefix. Version không tương thích vẫn bị loại. Pattern động vẫn là diagnostic.

## Ngoài phạm vi

Không nới rule này cho adapter khác nếu adapter đó không opt-in. Không đổi schema.

## Task

- TASK-RKG-028 — FastAPI static indexing coverage
