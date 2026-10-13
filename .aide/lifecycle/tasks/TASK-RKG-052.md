---
key: TASK-RKG-052
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-040
status: in_progress
revision: 2
authorization: CR-RKG-034
change_set: CHG-RKG-2026-019
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-052.yaml
  plan: PLAN-TASK-RKG-052.md
  diary: DIARY-TASK-RKG-052.md
  test: TEST-TASK-RKG-052-001.md
---
# TASK-RKG-052 — Go HTTP static route extraction

Story: STORY-RKG-040. Adapter `rkg.go-http` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-034 / CHG-RKG-2026-019. Không sửa `src/` trong lát hồ sơ này.

## Scope

Route Gin, chi và gorilla/mux tĩnh thành Endpoint method và path, với `handled_by` khi handler resolve một Callable. Không thực thi source. Deep support withheld.

## Ngoài phạm vi

Không thêm fact vào fixture event-worker. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-004, AC-RKG-006.

AC-RKG-004 và AC-RKG-006. `tests/conformance/test_go_http_framework.py` assert method, path, `handled_by` khi handler resolve một lần, diagnostic cho path động và handler bị che hoặc trùng tên, và không có cạnh `depends_on`.

## Chưa under test

AC-RKG-005 chưa under test: suite assert vắng `depends_on`, không assert chiều depends_on của AC. AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. Sentinel không nằm trong output không đủ để khai AC-RKG-016.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. Lát hồ sơ này chưa chạy pytest.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-052.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-052.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-052.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-052-001.md) — ot_run