---
uid:
key: STORY-RKG-011
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
satisfies: [AC-RKG-011, AC-RKG-018, AC-RKG-027, AC-RKG-054, AC-RKG-056, AC-RKG-057, AC-RKG-061]
classification: internal
ai_assisted: true
---
# STORY-RKG-011 — Explorer và quản lý repository trên API thật

## Giao cái gì

Thay mock client bằng client `/api/v1` mà không viết lại hành vi màn hình đã dựng ở STORY-RKG-001 và STORY-RKG-002. Onboarding, job, Explorer, evidence, dependency, technology và quản lý repository/snapshot chạy trên backend thật, cùng schema, state và accessibility.

## Ngoài phạm vi

Không đổi layout đã duyệt. Không thêm Q&A (STORY-RKG-014). Structure view thuộc `TASK-RKG-026` treo trực tiếp `EPIC-003-TEAM-RKG` (`STORY-RKG-016` đã deprecated).

## Task

- TASK-RKG-024 — Integrate UI with live API
