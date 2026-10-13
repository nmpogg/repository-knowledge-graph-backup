---
uid: null
key: STORY-RKG-016
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-003-TEAM-RKG
status: deprecated
revision: 4
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-003-TEAM-RKG
satisfies: []
classification: internal
ai_assisted: true
retirement_reason: Historical Structure slice has no separate current AC; TASK-RKG-026 belongs directly to its Epic.
---
# STORY-RKG-016 — Structure view trên Explorer

## Giao cái gì

Thêm nút Structure cạnh Graph và List. Cây lấy từ search của snapshot hiện tại, chọn lá mở đúng drawer chi tiết đang có. Lát cắt này dùng identity entity lúc bấy giờ (qualified name). Không thêm route, nav hay panel mới.

## Ngoài phạm vi

Chưa đổi canonical identity sang Directory. Việc đó là STORY-RKG-017; sau đó Structure dùng cùng Directory với Graph/List.

## Task (lịch sử — không còn containment hiện hành)

- TASK-RKG-026 — Structure view on Explorer *(hiện treo trực tiếp `EPIC-003-TEAM-RKG`; story này deprecated)*

## Revision 2

Revision 1 listed `AC-RKG-073`. The current AC text requires canonical Directory
identity, one selectable directory per path, and a compatibility projection for
old Namespace snapshots. That text is outside this story, which keeps the earlier
qualified-name Structure control and does not change canonical identity. Current
ownership is `STORY-RKG-017`. This story therefore has no current AC.

## Current containment

TASK-RKG-026 is directly under EPIC-003-TEAM-RKG. This retired Story preserves its ID; current Directory AC remains in STORY-RKG-017.
