---
uid:
key: STORY-RKG-017
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: done
revision: 2
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-002, AC-RKG-003, AC-RKG-007, AC-RKG-073]
classification: internal
ai_assisted: true
---
# STORY-RKG-017 — Directory thay Namespace trên snapshot mới

## Giao cái gì

Sau ADR-2026-006, core dựng Directory từ SourceUnit trong manifest. Snapshot mới không còn node Namespace. Import không lấy Directory làm đích. Snapshot cũ giữ nguyên ID, cạnh và pin conversation, đọc bằng projection tương thích. Structure, Graph và List chọn cùng một identity Directory.

## Ngoài phạm vi

Không tự re-index repository của người dùng. Không làm Java. Migration vật lý không phá snapshot đang có. Các pattern FastAPI còn hở thuộc STORY-RKG-018.

## Task

- TASK-RKG-027 — Directory entities and Namespace transition

## Revision 2

Current AC text points here and the AC entries point back:

- `AC-RKG-002` and `AC-RKG-003` describe Directory containment and import
  resolution without Namespace targets.
- `AC-RKG-073` describes Structure on those Directory identities.

`STORY-RKG-004` no longer lists `AC-RKG-002` or `AC-RKG-003`. `STORY-RKG-016`
and `STORY-RKG-019` no longer list `AC-RKG-073`.
