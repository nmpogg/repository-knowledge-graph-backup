---
uid:
key: STORY-RKG-038
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 1
authorization: CR-RKG-032
implementation_task: TASK-RKG-050
phase: code_present_lifecycle_backfill
change_set: CHG-RKG-2026-017
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-006]
classification: internal
ai_assisted: true
---
# STORY-RKG-038 — Express static route extraction

## Giao cái gì

Adapter `rkg.express` đã có trên cây. Route Express tĩnh thành Endpoint method và path, với `handled_by` khi callback cuối resolve một lần. Không thực thi source. Deep support withheld. `reviewed_deep_support` giữ false đối với adapter;
liên kết HTTP không đăng ký adapter mới. Hồ sơ này là backfill sau khi code đã có.

## Ngoài phạm vi

Không biến `use` thành Endpoint. Không HTTP `depends_on`. Không thăng deep-supported. Không ký gate. Không gắn change set này vào adapter_scope của CHG-RKG-2026-001.

## AC đang kiểm

AC-RKG-004 và AC-RKG-006. `tests/conformance/test_express_framework.py` assert method, path, `handled_by` khi handler resolve một lần, và diagnostic không tạo cạnh cho path động, receiver bị che, handler gán lại.

## Chưa under test

AC-RKG-005, AC-RKG-007, AC-RKG-016, AC-RKG-048 chưa under test. `validate_fact_batch` chạy nhưng không assert evidence location hay rule_id. Sentinel không nằm trong repr không đủ để khai AC-RKG-016.

## Task

- TASK-RKG-050 — Express static route extraction
