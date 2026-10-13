---
key: TASK-RKG-045
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-029
status: in_progress
revision: 7
authorization: CR-RKG-027
change_set: CHG-RKG-2026-012
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
  context: CTX-TASK-RKG-045.yaml
  plan: PLAN-TASK-RKG-045.md
  diary: DIARY-TASK-RKG-045.md
---
# TASK-RKG-045 — Java + Spring + JPA + Spring Kafka adapters

Story: STORY-RKG-029. Adapters `rkg.java` (language), `rkg.spring` (framework),
`rkg.jpa` (data_access), and `rkg.spring-kafka` (messaging) are implemented and
registered. Oracle: `repo-test/rkg-fixture-spring-orders`. Remaining work is
verify via conformance and spring census, plus deep-support review — not
closed. Task stays `in_progress` until verify + evidence.

## Scope

- Language (`rkg.java`): Java structure (SourceUnit/Type/Callable), imports,
  calls, class relations, syntax-error isolation with relative path, no-guess
  negatives (AC-RKG-003, AC-RKG-006, AC-RKG-007, AC-RKG-035, AC-RKG-048).
- Framework (`rkg.spring`): `@RestController`/`@Controller` static mappings →
  `Endpoint` method+path; `handled_by` (AC-RKG-004).
- Data access (`rkg.jpa`): `@Entity` + literal `@Table` → `DataResource`
  identity `relational:{schema}.{table}`; `maps_to`; Type-level `reads`/
  `writes` (AC-RKG-013, AC-RKG-014).
- Messaging (`rkg.spring-kafka`): unique topic constants; `KafkaTemplate.send`;
  `@KafkaListener` → `MessageChannel`; `publishes` / `consumes` (AC-RKG-015).
- Out of scope this task: new extractors; TypeScript/Vue/BullMQ/Go;
  deep-supported promotion; live eval/KPI; AC-RKG-005. Spring/Java
  constructor DI in REG is Type→Type `depends_on`, not AC-RKG-005
  Callable/Endpoint→Callable (FastAPI Depends-style).

## Acceptance criteria under test

AC-RKG-004, AC-RKG-006, AC-RKG-007, AC-RKG-013, AC-RKG-014, AC-RKG-015,
AC-RKG-048. Verify path: `tests/conformance/test_java_language.py`,
`tests/conformance/test_spring_stack.py`,
`tests/evaluation/test_spring_census.py`. Append evidence before marking done.

AC-RKG-003 and AC-RKG-035 remain an open Story obligation (STORY-RKG-029
satisfies) but are not asserted by `test_java_language.py`,
`test_spring_stack.py`, or `test_spring_census.py` (no import-edge assert; no
syntax-error sibling). See TEST-RKG-JAVA-SPRING-001.

## Result

Verify lát recorded: `TEST-RKG-JAVA-SPRING-001` (3 + 3 + 2 pytest passed on
commit `2d0af72…`) and `DIARY-TASK-RKG-045-r2`. Status remains `in_progress` —
deep-support review not closed.
