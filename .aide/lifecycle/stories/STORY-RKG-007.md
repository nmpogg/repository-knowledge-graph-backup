---
uid:
key: STORY-RKG-007
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
satisfies: [AC-RKG-008]
classification: internal
ai_assisted: true
---
# STORY-RKG-007 — Publish snapshot Kùzu nguyên tử

## Giao cái gì

Storage façade ghi candidate đã validate và đổi active pointer của đúng một repository trong một transaction ngắn. Lỗi thì rollback. Snapshot trước còn đọc được khi còn retained. Re-index thành công tạo snapshot mới, phản ánh file thêm, sửa và xóa.

## Ngoài phạm vi

Không điều phối job và không mở HTTP. Search/context thuộc STORY-RKG-008. Guard xóa và activate ở API thuộc STORY-RKG-010.

## Task

- TASK-RKG-013 — Kùzu storage and atomic snapshots
