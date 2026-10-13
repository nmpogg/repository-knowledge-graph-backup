---
uid:
key: STORY-RKG-036
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-030
implementation_task: TASK-RKG-048
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-015
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-006]
classification: internal
ai_assisted: true
---
# STORY-RKG-036 — Django static route extraction

## Giao cái gì

Adapter `rkg.django` đã có trên cây. Route Django tĩnh thành Endpoint method và path, với `handled_by` khi handler resolve một lần. Include và as_view theo suite. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không ORM. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-004 và AC-RKG-006. `tests/conformance/test_django_framework.py` assert method, path, `handled_by`, diagnostic `django_view_unresolved` / `django_include_unresolved`, và không gán method khi không có bằng chứng tĩnh.

## Chưa under test

AC-RKG-003, AC-RKG-005, AC-RKG-007, AC-RKG-015, AC-RKG-016, AC-RKG-035, AC-RKG-048 chưa under test. Suite không assert import, `depends_on`, `calls`, rule_id kèm evidence location, hay Configuration key. Việc sentinel không xuất hiện trong output không đủ để khai AC-RKG-016. Census so expected JSON không được gắn vào một AC id.

## Task

- TASK-RKG-048 — Django static route extraction
