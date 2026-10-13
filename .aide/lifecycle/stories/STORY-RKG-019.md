---
uid:
key: STORY-RKG-019
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-003-TEAM-RKG
status: done
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-003-TEAM-RKG]
satisfies: [AC-RKG-009, AC-RKG-010, AC-RKG-013]
classification: internal
ai_assisted: true
---
# STORY-RKG-019 — Luồng graph tập trung theo entity gốc

## Giao cái gì

Explorer và context thêm view flow: từ endpoint hoặc callable đi xuống call và truy cập; từ resource đi lên user rồi caller; từ type đi ra method và map. Overlay ownership và dependency là tùy chọn, không nuốt budget semantic. Receiver và data-access tĩnh đủ chắc mới tạo cạnh; method generic dùng chung không nối tới mọi bảng của caller.

## Ngoài phạm vi

Không thực thi source. Không đổi DDL. Re-index mới áp dụng extraction mới; snapshot và pin cũ giữ nguyên.

## Task

- TASK-RKG-029 — Focused entity flow graph

## Revision 2

Revision 1 listed `AC-RKG-073`. Current text of that AC is Directory structure
selection, owned by `STORY-RKG-017`. This story keeps traversal, context and
data-resource behavior only.
