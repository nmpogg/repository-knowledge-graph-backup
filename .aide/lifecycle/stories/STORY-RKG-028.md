---
uid:
key: STORY-RKG-028
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-026
implementation_task: TASK-RKG-044
verification_evidence: TEST-RKG-BULLMQ-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-011
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-015, AC-RKG-006, AC-RKG-007]
classification: internal
ai_assisted: true
---
# STORY-RKG-028 — BullMQ messaging extraction

## Giao cái gì

Messaging adapter `rkg.bullmq` trên oracle fixture
`repo-test/rkg-fixture-bullmq-worker`: Queue/Worker constructors thành
`MessageChannel` `channel_kind=queue`; Worker in callable → `consumes`;
resolved `queue.add` → `publishes`; không Redis URL/connection hay payload trên
graph; không HTTP `Endpoint` cho job schedulers / repeatables. Phụ thuộc
`rkg.typescript`.

## Ngoài phạm vi

Không đóng deep-support review. Không Vue/Nuxt/React Router/Java/Go. Không live
eval/KPI. Không deep set Python MVP.

## AC đang kiểm

AC-RKG-015, AC-RKG-006, AC-RKG-007 qua `tests/evaluation/test_bullmq_census.py`
và `expected_bullmq.json`. Không có suite conformance BullMQ riêng.

## Hiện trạng

`TEST-RKG-BULLMQ-001` ghi 2 pytest đã qua. `REV-RKG-STACK-SUPPORT-001` ghi
suite chưa assert `rule_id` của AC-RKG-007 và validate-before-publish.
Deep-supported vẫn đóng. Story ở `in_progress`.

## Task

- TASK-RKG-044 — BullMQ messaging adapter
