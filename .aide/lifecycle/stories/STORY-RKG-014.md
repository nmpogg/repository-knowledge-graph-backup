---
uid:
key: STORY-RKG-014
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-004-TEAM-RKG
status: done
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-004-TEAM-RKG]
satisfies: [AC-RKG-041, AC-RKG-046, AC-RKG-047, AC-RKG-059]
classification: internal
ai_assisted: true
---
# STORY-RKG-014 — API và UI hội thoại

## Giao cái gì

Người dùng tạo conversation, hỏi trên snapshot vừa index, mở citation và thao tác bằng keyboard. Session sai thì `401` trước provider. Thiếu revision hoặc `client_request_id` thì `422` và không tạo turn. Markdown từ repository hoặc model được thoát. Credential provider không ra browser, graph hay log.

## Ngoài phạm vi

Không đổi rubric trả lời đã chốt ở STORY-RKG-013. Không deploy production.

## Task

- TASK-RKG-021 — Conversation API and UI
