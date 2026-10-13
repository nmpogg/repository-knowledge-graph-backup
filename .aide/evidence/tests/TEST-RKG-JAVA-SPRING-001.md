---
key: TEST-RKG-JAVA-SPRING-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-045
captured_at: 2026-10-08
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 13 }
  - { key: STORY-RKG-029, revision: 1 }
  - { key: TASK-RKG-045, revision: 5 }
  - { key: PLAN-TASK-RKG-045, revision: 1 }
---

# TEST-RKG-JAVA-SPRING-001

Current-tree verification for Java language plus Spring, JPA, and Spring Kafka
adapters. Checked against the working tree on base commit above. No adapter
code changes in this verify lát; no edits under `src/rkg/adapters/**`. Plan:
[`PLAN-TASK-RKG-045.md`](../plans/PLAN-TASK-RKG-045.md). Diary append:
[`DIARY-TASK-RKG-045-r2.md`](../diaries/DIARY-TASK-RKG-045-r2.md).

Corpus context (spring-orders row):
[`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md`](TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md)
— `rkg-fixture-spring-orders` / java+spring+jpa+spring-kafka / 51 TP / 0 FN /
0 FP / coverage 1.0 / precision 1.0 / pass.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_java_language.py -v` | 3 passed |
| `pytest tests/conformance/test_spring_stack.py -v` | 3 passed |
| `pytest tests/evaluation/test_spring_census.py -v` | 2 passed |

## Contract rows (FR-RKG-002)

Map carefully to what the suites actually assert. Census oracle
`expected_spring.json` sets `allow_unlisted_actual` and `rule_id: null`.
AC-RKG-005 stays out of scope.

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-004 | Conformance `test_spring_endpoints_and_negatives`: Endpoint method+path for `GET /api/orders/{orderId}` and `GET`/`HEAD /api/orders/readiness`; `UnregisteredController` and `DynamicPathController` absent. Census oracle required attributes cover the six curated method+path Endpoints; prohibited rows repeat those two negatives. `handled_by` and registration chain are not asserted in either suite |
| AC-RKG-006 | Conformance: ambiguous `Marker` yields `java_binding_ambiguous` and no `depends_on` from `UsesMarker`; dynamic path yields no Endpoint; dynamic topic yields no `consumes`. Census prohibited rows cover dynamic path, dynamic-topic `consumes`, and `AmbiguousServices` `depends_on`. Star-import / instance-dispatch negatives are not in these suites |
| AC-RKG-007 | Corpus-level only: curated oracle rows carry relative `file_path` evidence and census compare matches that inventory. `rule_id` is null and `start_line` is null on those rows. `validate_fact_batch` runs in the conformance pipelines and does not assert evidence locations or rule ids. Full AC-007 validate-before-publish suite is not asserted here |
| AC-RKG-013 | Conformance: distinct `relational:commerce.orders`, `relational:commerce.order_items`, and `relational:audit.orders`; `maps_to` from the two commerce entities; no `reads`/`writes` onto `audit.orders`. Census inventories the same three DataResources (`name` + `namespace`) and the two commerce `maps_to` edges, with prohibited read/write onto `audit.orders`. Reflection/dynamic table negatives are not in these suites |
| AC-RKG-014 | Conformance: Type-level `reads` and `writes` from `persistence.JpaOrderRepository` to `relational:commerce.orders`, plus Callable `findById` `reads` and `save` `writes`. Census inventories the Type-level `reads`/`writes` pair only |
| AC-RKG-015 | Conformance: `publishes` `messaging.KafkaOrderEventPublisher.publish` → `orders.events`; `consumes` `messaging.PaymentEventListener.onPayment` → `payments.events`; `DynamicTopicListener` has no `consumes`. Census inventories `MessageChannel` `orders.events` and `payments.events` plus those two edges. Payload non-persistence is not asserted |
| AC-RKG-048 | Conformance `test_unique_implementer_calls_reach_repository_methods`: unique `calls` from `api.OrderController.get` to interface and sole implementer `getOrder`, and from `DefaultOrderService.getOrder` to interface and sole implementer `findById`. Call-site evidence, shadowed, module-level, and unresolved call negatives are not asserted. Census inventories one `calls` edge (`onPayment` → `applyPayment`); extra call facts are not false positives under `allow_unlisted_actual` |
| NFR-RKG-SEC-001 | Java conformance: secret sentinel and the datasource URL literal are absent from the entity/diagnostic blob. Census: sentinel absent from captured report text; oracle prohibited text forbids the sentinel. Not mapped to an extraction AC |

## What this verify asserted

| Claim | Covered by |
| --- | --- |
| Types, signature-qualified overloads, nested type, `inherits_from` | `test_java_language.py` |
| Type→Type constructor `depends_on` and configuration key names | `test_java_language.py` — Type→Type `depends_on` is outside AC-RKG-005 |
| Endpoint method+path and unregistered/dynamic negatives | `test_spring_stack.py`; fuller method+path inventory on the oracle via census |
| DataResource identity, `maps_to`, Type and Callable `reads`/`writes` | `test_spring_stack.py`; census is Type-level `reads`/`writes` plus identity |
| `publishes` / `consumes` and dynamic-topic negative | `test_spring_stack.py`; MessageChannel entities via census |
| Unique implementer `calls` | `test_spring_stack.py` |
| Oracle loads; three DataResource identities; census pass, coverage 1.0, precision 1.0 | `test_spring_census.py` |
| Secret sentinel absent from java fact blob and from census report text | both suites, as NFR-RKG-SEC-001 |
| Aggregate corpus row (51/0/0) | linked summary only — not rewritten this lát |

## Not asserted this turn

| Contract ID | Note |
| --- | --- |
| AC-RKG-003 | Import statements appear in fixtures. Neither conformance suite asserts import edges, and the census oracle has no import rows (`allow_unlisted_actual` treats extra import facts as non-FP) |
| AC-RKG-005 | Out of scope. Constructor DI in these suites is Type→Type `depends_on` |
| AC-RKG-035 | No syntax-error sibling in `test_java_language.py`, `test_spring_stack.py`, or the spring census oracle |

Deep-support promotion remains open; TASK-RKG-045 stays `in_progress`.
