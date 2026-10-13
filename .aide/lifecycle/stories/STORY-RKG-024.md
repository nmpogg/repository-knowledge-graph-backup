---
uid:
key: STORY-RKG-024
type: story
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-002-TEAM-RKG
status: in_progress
revision: 2
authorization: CR-RKG-028
implementation_task: TASK-RKG-046
verification_evidence: TEST-RKG-GO-KAFKA-PGX-001
phase: verified_deep_support_withheld
change_set: CHG-RKG-2026-013
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  part_of: [EPIC-002-TEAM-RKG]
satisfies: [AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015, AC-RKG-048]
classification: internal
ai_assisted: true
---
# STORY-RKG-024 — Go + kafka-go + pgx extraction

## Giao cái gì

Ba adapter `rkg.go` (language), `rkg.kafka-go` (messaging) và `rkg.pgx`
(data_access) đã implemented và đăng ký trong `builtin_adapters()`, selectable
theo mục draft `REG-ADAPTER-001`. Oracle:
`repo-test/rkg-fixture-go-event-worker`. `reviewed_deep_support = False`.
`rkg.kafka-go` và `rkg.pgx` phụ thuộc `rkg.go`. Go: Type/Callable, qualified
name theo package, không Namespace cho package; receiver value và pointer;
generic chỉ tên; `calls` tường minh; tên khóa env (`KAFKA_*`, `DATABASE_URL`,
`CLEANUP_INTERVAL`). kafka-go: `MessageChannel`; `consumes` từ
`NewKafkaReader`; `publishes` từ `EventPublisher.Publish` (topic/const tĩnh,
kể cả import alias). pgx: hằng SQL tĩnh `schema.table` thành `DataResource`
identity `relational:{schema}.{table}` (`kind=table`); method `reads` /
`writes`. Không mở entity type mới.

## Ngoài phạm vi

Không đóng deep-support review. Không TypeScript/Vue/BullMQ/Java. Không live
eval/KPI. Không deep set Python MVP. Không AC-RKG-005. Không extractor mới.

## AC đang kiểm

AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015, AC-RKG-048 qua
`tests/conformance/test_go_stack.py` và `tests/evaluation/test_go_census.py`.
AC-RKG-013 ở đây là identity `DataResource`; `maps_to` chưa được assert.
AC-RKG-007: oracle có `file_path` tương đối, `rule_id` và `start_line` null;
census không đối chiếu `file_path`. AC-RKG-003, AC-RKG-016 và AC-RKG-035 không
nằm trong suite này.

## Hiện trạng

`TEST-RKG-GO-KAFKA-PGX-001` ghi 3 + 2 pytest đã qua. Hiệu đính cách đọc
AC-RKG-007 nằm ở `TEST-RKG-GO-KAFKA-PGX-001-r2`.
`REV-RKG-STACK-SUPPORT-001` giữ `reviewed_deep_support = false`. Story ở
`in_progress`.

## Task

- TASK-RKG-046 — Go + kafka-go + pgx adapters
