---
uid:
key: STORY-RKG-010
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
satisfies: [AC-RKG-058, AC-RKG-061, AC-RKG-066, AC-RKG-067, AC-RKG-068, AC-RKG-069, AC-RKG-070, AC-RKG-071, AC-RKG-072]
classification: internal
ai_assisted: true
---
# STORY-RKG-010 — API repository, job, graph và session

## Giao cái gì

FastAPI v1 cho catalog, snapshot lifecycle, index job và các đọc graph/context. Session, Origin và Host sai thì `401` trước khi tạo job hoặc đọc source. Poll job theo `Retry-After`. Mismatch repository/snapshot trả `404` không lộ ownership. Locator và log được redact.

## Ngoài phạm vi

UI live thuộc STORY-RKG-011. Route conversation thuộc STORY-RKG-014. Contract Gate vẫn mở; lát cắt này bám `API-RKG-CORE-v1` đang pin, không tự nhận đã breaking-release.

## Task

- TASK-RKG-016 — Core FastAPI transport
