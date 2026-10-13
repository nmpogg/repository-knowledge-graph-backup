---
uid: null
key: TASK-RKG-026
type: task
group: normative
scope: lifecycle
system: SYS-RKG
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  part_of:
  - EPIC-003-TEAM-RKG
  depends_on:
  - TASK-RKG-017
  - TASK-RKG-024
  implements:
  - FR-RKG-003
classification: internal
ai_assisted: true
epic: EPIC-003-TEAM-RKG
implementation_record:
  context: CTX-TASK-RKG-026.yaml
  plan: PLAN-TASK-RKG-026.md
  diary: DIARY-TASK-RKG-026.md
---
# TASK-RKG-026 — Structure view on Explorer

Thêm nút Structure vào nhóm view Graph / List trên thanh Explorer. Bấm nút đổi
vùng canvas thành cây cấu trúc của snapshot hiện tại. Không route mới, không mục
nav, không tab drawer, không panel hay dialog mới.

## Phạm vi

- Nguồn cây là `GET /api/v1/entities` của snapshot, lấy hết trang. Không dựng từ
  subgraph.
- Nhóm theo `EntityType` theo thứ tự cố định, rồi tách `qualified_name` theo dấu
  `.`. `qualified_name` rỗng thì dùng `name`.
- Chọn lá dùng đúng lựa chọn entity và drawer chi tiết đang có, cùng đường với List.
- Graph, List, search, preset, direction, depth, max_nodes, export context, Ask,
  repository, job và conversation giữ nguyên. Không viết lại `KnowledgeGraph`.
- Revision 3 yêu cầu kiểm `AC-RKG-073` bằng test UI. Current text của AC đó
  thuộc `STORY-RKG-017`. Story của task này không còn `satisfies` AC đó.
  Không sửa `PLAN.md`.

## Hoàn tất

Evidence: `DIARY-TASK-RKG-026`, `TEST-RKG-UI-STRUCTURE`. Frontend lint (warning),
`tsc -b` và `npm test` pass trên cây làm việc tại `516f17e` cộng thay đổi chưa commit.
UI/UX Gate vẫn `pending`; không có approval mới. Chưa kiểm trên trình duyệt.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-026.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-026.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-026.md) — kết quả, evidence và các correction.
