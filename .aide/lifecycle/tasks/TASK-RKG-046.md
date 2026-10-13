---
key: TASK-RKG-046
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-024
status: in_progress
revision: 7
authorization: CR-RKG-028
change_set: CHG-RKG-2026-013
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-004
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-046.yaml
  plan: PLAN-TASK-RKG-046.md
  diary: DIARY-TASK-RKG-046.md
---
# TASK-RKG-046 — Go + kafka-go + pgx adapters

Story: STORY-RKG-024. Adapters `rkg.go` (language), `rkg.kafka-go` (messaging), and `rkg.pgx`
(data_access) are implemented and registered in `builtin_adapters()`. Oracle:
`repo-test/rkg-fixture-go-event-worker`. `REG-ADAPTER-001` has a draft section
for this stack. The MVP entries table lists `rkg.go`, `rkg.kafka-go`, and `rkg.pgx` (REG-ADAPTER-001 revision 17). Not deep-supported. Task stays
`in_progress`.

## Scope

- Language (`rkg.go`): `*.go` CST structure (Type/Callable); package-scoped
  qualified names; no Namespace for packages; value and pointer receivers;
  generics name-only; explicit `calls`; env key names (`KAFKA_*`,
  `DATABASE_URL`, `CLEANUP_INTERVAL`).
- Messaging (`rkg.kafka-go`): `MessageChannel`; `consumes` from
  `NewKafkaReader`; `publishes` from `EventPublisher.Publish` (static
  topic/const, including import alias).
- Data access (`rkg.pgx`): static SQL constants with `schema.table` →
  `DataResource` identity `relational:{schema}.{table}` (`kind=table`); method
  `reads`/`writes`.
- Out of scope this task: new extractors; TypeScript/Vue/BullMQ/Java;
  deep-supported promotion; live eval; AC-RKG-005. This stack has no
  Callable/Endpoint `depends_on` wiring.

## Acceptance criteria under test

AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015, AC-RKG-048.
Verify path: `tests/conformance/test_go_stack.py`,
`tests/evaluation/test_go_census.py`. Append evidence before marking done.

`test_go_stack.py` asserts Type/Callable structure, unique `calls` (including
the ambiguous-receiver negative), `MessageChannel` plus `publishes`/`consumes`
with dynamic-topic, package-level, and shadowed-kafka negatives, and
`DataResource` identity plus method `reads`/`writes`. `test_go_census.py`
matches `expected_go.json` for the same inventory. `validate_fact_batch` runs
in the conformance pipeline. AC-RKG-013 here is DataResource identity;
`maps_to` is not asserted. AC-RKG-007: oracle rows carry a relative
`file_path` with null `rule_id` and `start_line`. Census compare matches
type, qualified name, required attributes, and edge endpoints only. A null
oracle `rule_id` is not checked. `validate_fact_batch` only rejects a
non-relative entity path.

AC-RKG-003 and AC-RKG-035 are not under test. The suites do not assert import
edges, and they contain no syntax-error sibling. AC-RKG-016 is not under test:
env key names and sentinel absence appear in the suites; `depends_on` from
configuration users is not asserted.

## Result

Verify lát recorded: `TEST-RKG-GO-KAFKA-PGX-001` (`test_go_stack.py` 3 passed,
`test_go_census.py` 2 passed, on commit `2d0af72…`) and `DIARY-TASK-RKG-046`.
The AC-RKG-007 wording correction is `TEST-RKG-GO-KAFKA-PGX-001-r2`, and
`TEST-RKG-GO-KAFKA-PGX-001` remains the verify record.
Status remains `in_progress` — deep-support review not closed.
