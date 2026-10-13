---
uid:
key: STORY-RKG-029
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-027
implementation_task: TASK-RKG-045
verification_evidence: TEST-RKG-JAVA-SPRING-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-012
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-003, AC-RKG-004, AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015, AC-RKG-035, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-029 — Java + Spring + JPA + Spring Kafka extraction

## Giao cái gì

Bốn adapter `rkg.java` (language), `rkg.spring` (framework), `rkg.jpa`
(data_access) và `rkg.spring-kafka` (messaging) trên oracle fixture
`repo-test/rkg-fixture-spring-orders`. Java: cấu trúc SourceUnit/Type/Callable.
Spring: HTTP `Endpoint` method+path và `handled_by`. JPA: `DataResource`
identity `relational:{schema}.{table}`. Spring Kafka: `MessageChannel` với
`publishes` / `consumes`.

## Ngoài phạm vi

Không đóng deep-support review. Không TypeScript/Vue/BullMQ/Go. Không live
eval/KPI. Không deep set Python MVP. Không AC-RKG-005: constructor DI là
Type→Type `depends_on`, không phải Callable/Endpoint→Callable.

## AC đang kiểm

AC-RKG-004, AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015,
AC-RKG-048 qua `test_java_language.py`, `test_spring_stack.py` và
`test_spring_census.py`. AC-RKG-003 và AC-RKG-035 vẫn là nghĩa vụ của story
nhưng ba suite này chưa assert cạnh import và chưa có sibling syntax-error.

## Hiện trạng

`TEST-RKG-JAVA-SPRING-001` ghi 3 + 3 + 2 pytest đã qua.
`REV-RKG-STACK-SUPPORT-001` không thăng deep-supported vì thiếu assert import
của AC-RKG-003. Story ở `in_progress`.

## Task

- TASK-RKG-045 — Java + Spring + JPA + Spring Kafka adapters

## Note on AC-RKG-003

FR story ownership stays `STORY-RKG-017` on AC-RKG-003. This story verifies the
same AC on the Java fixture. Do not remove AC-003 from STORY-RKG-017 or edit FR.
