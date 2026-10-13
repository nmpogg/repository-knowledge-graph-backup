---
uid:
key: STORY-RKG-012
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-004-TEAM-RKG
status: done
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-004-TEAM-RKG]
satisfies: [AC-RKG-030, AC-RKG-031, AC-RKG-033, AC-RKG-044, AC-RKG-045]
classification: internal
ai_assisted: true
---
# STORY-RKG-012 — Lưu conversation và pin snapshot

## Giao cái gì

Conversation, turn và focus bền trong cùng Kùzu, pin đúng repository/snapshot. Reload không làm mất history. Snapshot mới không kéo conversation cũ. Retry cùng `client_request_id` không nhân đôi turn. Xóa bị chặn khi còn turn pending hoặc còn reference.

Revision 1 liệt kê `AC-RKG-032`. `TASK-RKG-018` ghi history window được kiểm ở `TASK-RKG-020`. Revision này bỏ AC đó khỏi `satisfies` của story persistence. Hỏi tiếp khi vượt window thuộc STORY-RKG-013.

## Ngoài phạm vi

Chưa gọi provider và chưa có màn hình hỏi đáp. Grounded answer thuộc STORY-RKG-013. HTTP và UI thuộc STORY-RKG-014.

## Task

- TASK-RKG-018 — Conversation persistence and state
