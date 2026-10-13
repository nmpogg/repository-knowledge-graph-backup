---
uid:
key: STORY-RKG-001
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-001-TEAM-RKG
status: done
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-001-TEAM-RKG]
satisfies: [AC-RKG-027, AC-RKG-043, AC-RKG-011, AC-RKG-018, AC-RKG-054, AC-RKG-056, AC-RKG-057, AC-RKG-061, AC-RKG-066, AC-RKG-068]
classification: internal
ai_assisted: true
---
# STORY-RKG-001 — Onboarding, theo dõi job và Explorer trên mock

## Giao cái gì

Lát cắt UI đầu của M0. Người dùng đăng ký repository local, theo dõi job, rồi search, duyệt graph, mở evidence và xuất context trên mock client đúng hình dạng `API-RKG-CORE-v1`. Chọn application candidate không tự chọn sẵn. Panel dependency và technology giữ đúng support state. Phần tạo repository và mở graph sau index của AC-RKG-054/061/066/068 nằm ở lát cắt này. Keyboard, focus và trạng thái loading/empty/error đi theo `UXF-RKG-001`, `SCR-RKG-001` và `UIS-RKG-001`.

## Ngoài phạm vi

Không gọi backend thật (việc đó thuộc STORY-RKG-011). Không làm màn quản lý xóa/activate snapshot (STORY-RKG-002). Không nhúng Q&A.

## Task

- TASK-RKG-017 — MVP UI with mock client
