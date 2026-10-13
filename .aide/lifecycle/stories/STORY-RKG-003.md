---
uid:
key: STORY-RKG-003
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
satisfies: [AC-RKG-001, AC-RKG-026, AC-RKG-051, AC-RKG-049, AC-RKG-050]
classification: internal
ai_assisted: true
---
# STORY-RKG-003 — Nạp source local mà không thực thi

## Giao cái gì

Lát cắt ingestion. Index một repository local thành manifest bất biến, không import source và không tạo side effect. Path ngoài allowlist, symlink thoát root, quá số file hoặc quá dung lượng file bị chặn hoặc bỏ qua theo AC, không lộ absolute host path.

## Ngoài phạm vi

Không parse AST, không chọn adapter, không ghi Kùzu.

## Task

- TASK-RKG-003 — Local source loader
