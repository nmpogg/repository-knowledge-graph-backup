---
uid:
key: STORY-RKG-025
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-029
implementation_task: TASK-RKG-047
verification_evidence: TEST-RKG-FLASK-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-014
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-004, AC-RKG-005, AC-RKG-006, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-025 — Flask static route extraction

## Giao cái gì

Adapter `rkg.flask` đã đăng ký, capability `DETECTED_ONLY`, trích route Flask
tĩnh. `reviewed_deep_support = False`. Adapter này không phải profile
deep-supported đã review. Suite:
`tests/conformance/test_flask_framework.py`. Parse phụ thuộc `rkg.python`.
Không có oracle repo-test.

## Ngoài phạm vi

Không đóng deep-support. Không TypeScript, Vue, BullMQ, Java hay Go. Không live
eval. Không extractor mới. AC-RKG-007 không thuộc claim evidence-path của story
này.

## AC đang kiểm

AC-RKG-004, AC-RKG-005, AC-RKG-006, AC-RKG-048 qua
`tests/conformance/test_flask_framework.py`: method, path, `handled_by`,
`depends_on`, `calls`, và các negative dynamic route, callable chưa đăng ký,
module flask cục bộ, app mơ hồ. Không có oracle repo-test và không có census.
AC-RKG-003, AC-RKG-007 và AC-RKG-035 không thuộc suite này.

## Hiện trạng

`TEST-RKG-FLASK-001` ghi 3 pytest đã qua. Hiệu đính cách đọc AC-RKG-004 nằm ở
`TEST-RKG-FLASK-001-r2`. Capability giữ `DETECTED_ONLY`.
`REV-RKG-STACK-SUPPORT-001` không thăng deep-supported. Story ở `in_progress`.

## Task

- TASK-RKG-047 — Flask static route adapter
