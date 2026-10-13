---
key: TEST-RKG-GO-KAFKA-PGX-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-046
captured_at: 2026-10-08
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 14 }
  - { key: STORY-RKG-024, revision: 1 }
  - { key: TASK-RKG-046, revision: 3 }
  - { key: PLAN-TASK-RKG-046, revision: 1 }
---

# TEST-RKG-GO-KAFKA-PGX-001

Current-tree verification for Go language plus kafka-go and pgx adapters.
Checked against the working tree on base commit above. No edits under `src/`
in this verify lát. Plan:
[`PLAN-TASK-RKG-046.md`](../plans/PLAN-TASK-RKG-046.md). Diary:
[`DIARY-TASK-RKG-046.md`](../diaries/DIARY-TASK-RKG-046.md).

Corpus context (go event-worker row):
[`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md`](TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md)
— `rkg-fixture-go-event-worker` / go+kafka-go+pgx / 41 TP / 0 FN / 0 FP /
coverage 1.0 / precision 1.0 / pass. Linked only; the full corpus was not
re-run this lát.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_go_stack.py -v` | 3 passed |
| `pytest tests/evaluation/test_go_census.py -v` | 2 passed |

## Contract rows (FR-RKG-002)

Map carefully to what the suites actually assert. Census oracle
`expected_go.json` sets `allow_unlisted_actual`. `rule_id` is null and
`start_line` is null on oracle rows. The suites agree with the task under-test
list except AC-RKG-007 path equality, noted on that row.

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-006 | Conformance `test_kafka_go_channels_and_negatives`: no `publishes` whose source contains `dynamic_topic`, `package_level_publish`, or `shadowed_package`; no `calls` whose target ends with `firstWorker.Work` or `secondWorker.Work`. Census prohibited rows cover those four negatives. Diagnostics that explain unresolved or unsupported targets are not asserted. Star-import and instance-dispatch negatives are not in these suites |
| AC-RKG-007 | Oracle rows carry relative `file_path` values with `rule_id` null and `start_line` null. Census compare matches type, qualified name, required attributes, and edge endpoints; it does not compare `file_path`, and a null oracle `rule_id` does not require the actual `rule_id` to be null. `validate_fact_batch` runs in the conformance pipeline and rejects a non-relative entity path; the tests do not assert oracle locations or rule ids. Full AC-007 validate-before-publish suite is not asserted here. This is narrower than the task sentence that treats AC-RKG-007 as verified corpus-level evidence paths |
| AC-RKG-013 | Conformance `test_pgx_static_sql_reads_writes`: DataResource `relational:commerce.order_projection` with `kind=table`, `namespace=commerce`, `name=order_projection`. Census oracle required attributes match that identity; `test_expected_oracle_loads` checks the qualified name. `maps_to` is not asserted. Reflection and dynamic-table negatives are not in these suites |
| AC-RKG-014 | Conformance: Callable `reads` from `storage.PostgresRepository.FindByID` and `writes` from `Upsert` and `DeleteOlderThan` to `relational:commerce.order_projection`. Census inventories the same three edges. Type-level `reads`/`writes` and operation metadata are not asserted |
| AC-RKG-015 | Conformance: MessageChannel `orders.events` and `orders.projection.updated` with matching `name`; `consumes` `messaging.NewKafkaReader` → `orders.events`; `publishes` `messaging.EventPublisher.Publish` → `orders.projection.updated`; dynamic-topic, package-level, and shadowed-kafka `publishes` absent. Census inventories the two channels and those two edges, plus the same prohibited publish rows. Payload non-persistence is not asserted |
| AC-RKG-048 | Conformance language test: `calls` `main` → `run`, `app.Processor.HandleMessage` → `app.Processor.Process`, `app.Processor.Process` → `domain.DecodeEvent`, `storage.OrderRepository.Upsert`, and `messaging.EventPublisher.Publish`, and `app.Cleanup.Run` → `storage.OrderRepository.DeleteOlderThan`. Kafka test: `messaging.KafkaConsumer.Run` → `messaging.MessageHandler.HandleMessage`, plus the ambiguous-receiver negative. Pgx test: `storage.PostgresRepository.FindByID` → `storage.PgxDB.QueryRow`. Census inventories the language and kafka `calls` rows in `expected_go.json`; the QueryRow edge is not an oracle row and is not a false positive under `allow_unlisted_actual`. Call-site evidence is not asserted |
| NFR-RKG-SEC-001 | Conformance: secret sentinel absent from the entity and diagnostic blob. Census: sentinel absent from captured report text; oracle prohibited text forbids the sentinel. Not mapped to an extraction AC |

## What this verify asserted

| Claim | Covered by |
| --- | --- |
| Type and Callable names, value and pointer receivers, generic function name, no Namespace entities | `test_go_stack.py` (`test_go_language_types_calls_config_and_no_namespace`); census oracle load also rejects Namespace entities |
| Environment configuration key names (`KAFKA_BROKERS`, `KAFKA_GROUP_ID`, `DATABASE_URL`, `CLEANUP_INTERVAL`) | `test_go_language_types_calls_config_and_no_namespace`; census Configuration rows. Not an AC-RKG-016 `depends_on` assert |
| MessageChannel, `publishes` / `consumes`, and dynamic, package-level, and shadowed negatives | `test_kafka_go_channels_and_negatives`; census inventory and prohibited rows |
| DataResource identity and method `reads` / `writes` | `test_pgx_static_sql_reads_writes`; census identity and the three edges |
| Unique `calls`, including ambiguous-receiver negative | `test_go_stack.py`; census `calls` rows and prohibited ambiguous-receiver calls |
| Oracle loads; DataResource identity present; census pass, coverage 1.0, precision 1.0 | `test_go_census.py` |
| Secret sentinel absent from the conformance blob and from census report text | both suites, as NFR-RKG-SEC-001 |
| Host path string absent from the conformance blob and from census report text | both suites; data minimization, not an extraction AC |
| Aggregate corpus row (41/0/0) | linked summary only — not rewritten and not re-run this lát |

## Not asserted this turn

| Contract ID | Note |
| --- | --- |
| AC-RKG-003 | Import statements appear in fixtures, including an import alias on the positive publish case. Neither suite asserts import edges. The census oracle has no import rows (`allow_unlisted_actual` treats extra import facts as non-FP) |
| AC-RKG-005 | No Callable or Endpoint `depends_on` wiring is asserted |
| AC-RKG-016 | Env key names and sentinel absence appear. `depends_on` from configuration users is not asserted. Sentinel absence is NFR-RKG-SEC-001 |
| AC-RKG-035 | No syntax-error sibling in `test_go_stack.py`, `test_go_census.py`, or the go census oracle |
| `maps_to` | Absent from conformance asserts and from `expected_go.json` edges. AC-RKG-013 in this lát is DataResource identity only |

Deep-support promotion remains open; TASK-RKG-046 stays `in_progress`.
