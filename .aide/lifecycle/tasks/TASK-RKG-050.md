---
key: TASK-RKG-050
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-038
status: in_progress
revision: 3
authorization: CR-RKG-032
change_set: CHG-RKG-2026-017
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
  context: CTX-TASK-RKG-050.yaml
  plan: PLAN-TASK-RKG-050.md
  diary: DIARY-TASK-RKG-050.md
  test: TEST-TASK-RKG-050-001.md
---
# TASK-RKG-050 — Express static route extraction

Story: STORY-RKG-038. Adapter `rkg.express` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-032 / CHG-RKG-2026-017. Không sửa `src/` trong lát hồ sơ này.

## Scope

Route Express tĩnh thành Endpoint method và path, với `handled_by` khi callback cuối resolve một lần. Không thực thi source. Deep support withheld.

## Ngoài phạm vi

Không biến `use` thành Endpoint. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-004, AC-RKG-006, AC-RKG-007.

AC-RKG-004 và AC-RKG-006. `tests/conformance/test_express_framework.py` assert method, path, `handled_by` khi handler resolve một lần, và diagnostic không tạo cạnh cho path động, receiver bị che, handler gán lại.

## Chưa under test

AC-RKG-007 đã có assert rule id và evidence location (`TEST-RKG-AC007-ASSERT-001`, passed). AC-RKG-005, AC-RKG-016, AC-RKG-048 chưa under test. Sentinel không nằm trong repr không đủ để khai AC-RKG-016. Status stays `in_progress`.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. TEST-RKG-AC007-ASSERT-001 ghi passed cho assert rule id và evidence location. Census trong plan không nằm trong lần chạy đó. Task chưa done.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-050.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-050.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-050.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-050-001.md) — ot_run