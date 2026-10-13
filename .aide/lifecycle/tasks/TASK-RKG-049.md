---
key: TASK-RKG-049
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-037
status: in_progress
revision: 2
authorization: CR-RKG-031
change_set: CHG-RKG-2026-016
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
  context: CTX-TASK-RKG-049.yaml
  plan: PLAN-TASK-RKG-049.md
  diary: DIARY-TASK-RKG-049.md
  test: TEST-TASK-RKG-049-001.md
---
# TASK-RKG-049 — Next static route and navigation extraction

Story: STORY-RKG-037. Adapter `rkg.next` đã có trên cây. Task stays `in_progress`. This record is a lifecycle backfill. It does not mark the task done.

## Làm gì

Đối chiếu code và suite đã có với CR-RKG-031 / CHG-RKG-2026-016. Không sửa `src/` trong lát hồ sơ này.

## Scope

Route Next tĩnh (page, route handler, pages API có verb literal) và navigation `calls` khi target resolve đúng một route. Không thực thi source. Deep support withheld.

## Ngoài phạm vi

Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## Acceptance criteria under test

AC-RKG-004, AC-RKG-006, AC-RKG-048.

AC-RKG-004, AC-RKG-006 và AC-RKG-048. `tests/conformance/test_next_framework.py` assert HTTP method và path, navigation path, `handled_by`, `calls` `RKG.next.navigation.v1` kèm evidence id, và diagnostic không tạo cạnh cho href động, binding bị che, route mơ hồ, handler chưa resolve.

## Chưa under test

AC-RKG-003, AC-RKG-005, AC-RKG-007, AC-RKG-016, AC-RKG-035 chưa under test. Suite assert không có cạnh `depends_on` tới Endpoint trong các case đó. Sentinel không nằm trong output không đủ để khai AC-RKG-016. `evidence_ids` khác rỗng không assert rule_id và location của AC-RKG-007.

## Xong khi

Suite nêu trong plan được chạy trên cây này và evidence ghi kết quả, gate vẫn chỉ `pending` cho đến khi có chữ ký, và deep support vẫn withheld. Lát hồ sơ này chưa chạy pytest.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-049.yaml)
- [Plan](../../evidence/plans/PLAN-TASK-RKG-049.md)
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-049.md)
- [Test evidence](../../evidence/tests/TEST-TASK-RKG-049-001.md) — ot_run