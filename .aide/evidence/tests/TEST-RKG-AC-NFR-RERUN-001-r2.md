---
key: TEST-RKG-AC-NFR-RERUN-001-r2
type: test-evidence
group: evidence
system: SYS-RKG
status: recorded
revision: 2
captured_at: 2026-10-08
captured_against:
  code_commit: 4c6ab37789eda0cd820c86313bef1e71359eacb0
  working_tree: dirty
  prior: TEST-RKG-AC-NFR-RERUN-001
---

# TEST-RKG-AC-NFR-RERUN-001-r2 — AC/NFR re-run matrix

Append-only revision. Does not edit `TEST-RKG-AC-NFR-RERUN-001.md`. Does not
mark a story, task, epic, or gate done. Does not sign an approval. Each AC and
each NFR item has exactly one `rerun` status: `passed`, `failed`, or `not_run`.

## Tree

`git rev-parse HEAD` = `4c6ab37789eda0cd820c86313bef1e71359eacb0`. The tree is
**dirty**. Uncommitted product edits remain under
`frontend/src/components/graph/KnowledgeGraph.tsx`,
`frontend/src/components/graph/graphLayout.ts`, and
`frontend/src/components/graph/graphLayout.test.ts`. `tests/evals/.gitkeep` is
deleted. Those product files were not modified by this revision.

A measurement taken on that dirty frontend tree is not a clean pass. Revision 1
`npm test` (13 files, 77 passed) and `npx tsc -b --pretty false` ran while those
graph files were uncommitted. This revision does not treat that frontend output
as `passed`.

## Commands this revision

None. No suite was re-run. Analyzed-repository source was not executed.

Revision 1 backend output still supports the rows kept `passed` below:
`uv run pytest tests -q -rs --tb=no` recorded 246 passed, 7 skipped, 0 failed.
Skipped cases stay `not_run` (symlink creation not permitted; OpenRouter
credential unavailable; sibling pilot repository unavailable). That pytest
command runs `tests/` and does not import
`frontend/src/components/graph/`. Every row kept `passed` in this revision is
one whose revision-1 status was already `passed` solely on that pytest output.
Nothing is promoted to `passed`.

## FIND-RKG-TE-001

FR-RKG-001 defines one criterion, AC-RKG-072, with two `validated_by` targets
(`TEST-RKG-REPOSITORY-ISOLATION`, `TEST-RKG-REPOSITORY-MANAGEMENT-A11Y`). They
are the same AC, not two acceptance items. This revision has one AC-RKG-072
row. Isolation was `passed` in revision 1 and management accessibility was
`not_run`, so the single status is `not_run`.

## FIND-RKG-TE-002

The tree is recorded dirty. Rows whose revision-1 `passed` depended on the
frontend suite are set to `not_run`: AC-RKG-073, AC-RKG-046, and
NFR-RKG-UX-001#5. Rows that were already `not_run` stay `not_run`.

## Matrix counts

119 items. `passed` 59. `failed` 0. `not_run` 60.

## FR-RKG-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-001 | TEST-RKG-SCAN-SAFE | not_run | not_run |
| AC-RKG-026 | TEST-RKG-INDEX-INJECTION | TEST-RKG-CORE-API-001 | passed |
| AC-RKG-034 | TEST-RKG-INDEX-SINGLE-WRITER | TEST-RKG-CORE-API-001; TEST-RKG-INDEX-JOB-CLI-001 | passed |
| AC-RKG-051 | TEST-RKG-SOURCE-BOUNDARY | not_run | not_run |
| AC-RKG-055 | TEST-RKG-CLI | TEST-RKG-INDEX-JOB-CLI-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-008 | TEST-RKG-REINDEX | TEST-RKG-INDEX-JOB-CLI-001; TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| AC-RKG-012 | TEST-RKG-PARTIAL-ERRORS | TEST-RKG-INDEX-JOB-CLI-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-049 | TEST-RKG-FILE-LIMIT | TEST-RKG-INDEX-JOB-CLI-001 | passed |
| AC-RKG-050 | TEST-RKG-LARGE-FILE-SKIP | TEST-RKG-INDEX-JOB-CLI-001 | passed |
| AC-RKG-038 | TEST-RKG-SCAN-REPORT | TEST-RKG-INDEX-JOB-CLI-001 | passed |
| AC-RKG-039 | TEST-RKG-SCAN-BENCHMARK | TEST-RKG-PERF-SUMMARY-001 | not_run |
| AC-RKG-027 | TEST-RKG-ONBOARDING-E2E | not_run | not_run |
| AC-RKG-043 | TEST-RKG-ONBOARDING-SELECTION | not_run | not_run |
| AC-RKG-054 | TEST-RKG-LOCAL-ONBOARDING-E2E | not_run | not_run |
| AC-RKG-058 | TEST-RKG-INDEX-SESSION | TEST-RKG-CORE-API-001 | passed |
| AC-RKG-061 | TEST-RKG-JOB-POLLING | TEST-RKG-CORE-API-001 | passed |
| AC-RKG-066 | TEST-RKG-REPOSITORY-CRUD | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-067 | TEST-RKG-REPOSITORY-UPDATE | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-INDEX-JOB-CLI-001 | passed |
| AC-RKG-068 | TEST-RKG-REPOSITORY-SNAPSHOT-HISTORY | TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| AC-RKG-069 | TEST-RKG-SNAPSHOT-ACTIVATE | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-070 | TEST-RKG-SNAPSHOT-DELETE-GUARD | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-071 | TEST-RKG-REPOSITORY-DELETE-GUARD | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-072 | TEST-RKG-REPOSITORY-ISOLATION, TEST-RKG-REPOSITORY-MANAGEMENT-A11Y | TEST-RKG-CORE-API-001; not_run | not_run |

AC-RKG-061 stays `passed` on pytest `tests/integration/test_core_api.py` only.
It does not use the frontend suite. AC-RKG-072 is one row: management
accessibility had no test-evidence file, so the AC is `not_run`.

## FR-RKG-002

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-002 | TEST-RKG-SOURCE-STRUCTURE | not_run | not_run |
| AC-RKG-035 | TEST-RKG-SYNTAX-DIAGNOSTIC | TEST-RKG-VUE-NUXT-001 | not_run |
| AC-RKG-004 | TEST-RKG-ENDPOINT-EXTRACTION | TEST-RKG-FASTAPI-ADAPTER-001 | passed |
| AC-RKG-005 | TEST-RKG-DECLARED-DEPENDENCY | TEST-RKG-FASTAPI-ADAPTER-001 | passed |
| AC-RKG-003 | TEST-RKG-IMPORT-RESOLVE | TEST-RKG-FOCUSED-FLOW-001; TEST-RKG-TYPESCRIPT-REACT-ROUTER-001; TEST-RKG-VUE-NUXT-001 | not_run |
| AC-RKG-006 | TEST-RKG-NO-GUESS | TEST-RKG-FASTAPI-ADAPTER-001 | passed |
| AC-RKG-007 | TEST-RKG-EVIDENCE | TEST-RKG-FASTAPI-ADAPTER-001 | not_run |
| AC-RKG-048 | TEST-RKG-CALL-RESOLVE | TEST-RKG-VUE-NUXT-001; TEST-RKG-JAVA-SPRING-001; TEST-RKG-GO-KAFKA-PGX-001; TEST-RKG-FLASK-001 | not_run |
| AC-RKG-013 | TEST-RKG-DB-MAPS | TEST-RKG-SQLALCHEMY-ADAPTER-001 | passed |
| AC-RKG-014 | TEST-RKG-DB-RW | TEST-RKG-SQLALCHEMY-ADAPTER-001 | passed |
| AC-RKG-015 | TEST-RKG-EVENT | TEST-RKG-AIOKAFKA-ADAPTER-001 | passed |
| AC-RKG-016 | TEST-RKG-CONFIG | TEST-RKG-CONFIG | passed |
| AC-RKG-017 | TEST-RKG-CLASS-REL | TEST-RKG-CONFIG | passed |
| AC-RKG-020 | TEST-RKG-DETECT | TEST-RKG-DETECT-001 | passed |
| AC-RKG-021 | TEST-RKG-DETECT-NEG | TEST-RKG-DETECT-001; TEST-RKG-PKG-INVENTORY | passed |
| AC-RKG-040 | TEST-RKG-DETECTION-OVERRIDE | TEST-RKG-DETECT-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-052 | TEST-RKG-APP-AUTOSELECT | TEST-RKG-DETECT-001 | passed |
| AC-RKG-053 | TEST-RKG-MULTI-ADAPTER | TEST-RKG-DETECT-001 | passed |
| AC-RKG-065 | TEST-RKG-APP-UNRESOLVED | TEST-RKG-DETECT-001 | passed |
| AC-RKG-022 | TEST-RKG-PKG-INVENTORY | TEST-RKG-PKG-INVENTORY | passed |
| AC-RKG-023 | TEST-RKG-HTTP-INVENTORY | TEST-RKG-HTTP-INVENTORY | passed |

AC-RKG-003, AC-RKG-007, AC-RKG-035, and AC-RKG-048 stay `not_run`. Java, Go,
Flask, and/or BullMQ evidence still records those asserts as absent.

## FR-RKG-003

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-009 | TEST-RKG-TRAVERSAL | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-036 | TEST-RKG-SEARCH | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-037 | TEST-RKG-QUERY-BENCHMARK | TEST-RKG-GRAPH-READS-001 | not_run |
| AC-RKG-060 | TEST-RKG-NO-ACTIVE-SNAPSHOT | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-011 | TEST-RKG-UI-EXPLORER | not_run | not_run |
| AC-RKG-018 | TEST-RKG-UI-PRESETS | not_run | not_run |
| AC-RKG-056 | TEST-RKG-UI-VISUAL-A11Y | not_run | not_run |
| AC-RKG-057 | TEST-RKG-UI-TECH-DEPENDENCY | not_run | not_run |
| AC-RKG-073 | TEST-RKG-UI-STRUCTURE | TEST-RKG-UI-STRUCTURE | not_run |

AC-RKG-037 stays `not_run` (p95 benchmark not executed). AC-RKG-073 is `not_run`
because revision 1 marked it `passed` from `npm test`, which executed the dirty
frontend graph files.

## FR-RKG-004

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-010 | TEST-RKG-CONTEXT | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-062 | TEST-RKG-CONTEXT-BENCHMARK | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | not_run |

AC-RKG-062 stays `not_run`. The context p95 benchmark was not executed.

## FR-RKG-005

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-024 | TEST-RKG-QA-EVAL | TEST-RKG-QA-EVAL-SUMMARY-001-r4; TEST-RKG-QA-EVAL-001-r6 | not_run |
| AC-RKG-025 | TEST-RKG-QA-NEGATIVE | TEST-RKG-GROUNDED-QA-001 | passed |
| AC-RKG-041 | TEST-RKG-LOCAL-SESSION | TEST-RKG-CONVERSATION-API-001 | passed |
| AC-RKG-042 | TEST-RKG-QA-INJECTION | TEST-RKG-CONVERSATION-API-001; TEST-RKG-GROUNDED-QA-001 | passed |
| AC-RKG-047 | TEST-RKG-LOCAL-QA-E2E | TEST-RKG-CONVERSATION-API-001 | passed |
| AC-RKG-063 | TEST-RKG-LLM-LIMITS | TEST-RKG-LLM-LIMITS; TEST-RKG-CONVERSATION-API-001; TEST-RKG-GROUNDED-QA-001 | not_run |
| AC-RKG-028 | TEST-RKG-FOLLOWUP | TEST-RKG-CONVERSATION-API-001; TEST-RKG-GROUNDED-QA-001 | not_run |
| AC-RKG-029 | TEST-RKG-CLARIFY | TEST-RKG-CONVERSATION-API-001; TEST-RKG-GROUNDED-QA-001 | passed |
| AC-RKG-030 | TEST-RKG-HISTORY-PERSIST | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-031 | TEST-RKG-SNAPSHOT-PIN | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-032 | TEST-RKG-HISTORY-WINDOW | TEST-RKG-GROUNDED-QA-001; TEST-RKG-CONVERSATION-API-001 | passed |
| AC-RKG-033 | TEST-RKG-TURN-GUARD | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-044 | TEST-RKG-SNAPSHOT-RETENTION | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-045 | TEST-RKG-CONVERSATION-DELETE-GUARD | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-046 | TEST-RKG-CONVERSATION-A11Y | TEST-RKG-CONVERSATION-API-001 | not_run |
| AC-RKG-059 | TEST-RKG-TURN-REQUIRED-FIELDS | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-064 | TEST-RKG-CONVERSATION-REDACTION | TEST-RKG-CONVERSATION-STATE-001 | passed |

AC-RKG-024, AC-RKG-028, and AC-RKG-063 stay `not_run` (live eval, live
follow-up, and partial LLM limits were not a completed pass). AC-RKG-041,
AC-RKG-042, AC-RKG-047, AC-RKG-029, and AC-RKG-032 stay `passed` only because
revision 1 pytest ran the backend tests named in those evidence files
(`tests/integration/`), not because of `npm test`. AC-RKG-046 is `not_run`
because revision 1 marked it `passed` from `ConversationPage.test.tsx` in the
frontend suite.

## NFR-RKG-PERF-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-PERF-001#benchmark-corpus | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |
| NFR-RKG-PERF-001#reference-host | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |
| NFR-RKG-PERF-001#full-scan-wall-time | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |
| NFR-RKG-PERF-001#analyzer-peak-ram | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |
| NFR-RKG-PERF-001#search-subgraph-p95 | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |
| NFR-RKG-PERF-001#context-api-p95 | NFR threshold table | TEST-RKG-PERF-SUMMARY-001 | not_run |

## NFR-RKG-SEC-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-SEC-001#1 | normative item 1 deployment surface | not_run | not_run |
| NFR-RKG-SEC-001#2 | normative item 2 server-owned config | not_run | not_run |
| NFR-RKG-SEC-001#3 | normative item 3 local source boundary | not_run | not_run |
| NFR-RKG-SEC-001#4 | normative item 4 analyzer isolation | not_run | not_run |
| NFR-RKG-SEC-001#5 | normative item 5 data minimization | TEST-RKG-VUE-NUXT-001; TEST-RKG-BULLMQ-001; TEST-RKG-JAVA-SPRING-001; TEST-RKG-GO-KAFKA-PGX-001; TEST-RKG-CONVERSATION-STATE-001 | not_run |
| NFR-RKG-SEC-001#6 | normative item 6 LLM control plane | not_run | not_run |
| NFR-RKG-SEC-001#7 | normative item 7 repository lifecycle | not_run | not_run |
| NFR-RKG-SEC-001#8 | normative item 8 cross-repository isolation | not_run | not_run |

## NFR-RKG-REL-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-REL-001#1 | normative item 1 single writer | TEST-RKG-CORE-API-001; TEST-RKG-INDEX-JOB-CLI-001 | passed |
| NFR-RKG-REL-001#2 | normative item 2 repository ownership | TEST-RKG-CORE-API-001; TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| NFR-RKG-REL-001#3 | normative item 3 atomic publish/activate | TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| NFR-RKG-REL-001#4 | normative item 4 pinned reads | TEST-RKG-GRAPH-READS-001; TEST-RKG-CONVERSATION-STATE-001 | passed |
| NFR-RKG-REL-001#5 | normative item 5 immutable snapshots | TEST-RKG-INDEX-JOB-CLI-001; TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| NFR-RKG-REL-001#6 | normative item 6 delete/retention guards | TEST-RKG-STORAGE-SNAPSHOTS-001; TEST-RKG-CONVERSATION-STATE-001 | passed |
| NFR-RKG-REL-001#7 | normative item 7 optimistic repository update | TEST-RKG-STORAGE-SNAPSHOTS-001 | passed |
| NFR-RKG-REL-001#8 | normative item 8 conversation concurrency | TEST-RKG-CONVERSATION-STATE-001 | passed |
| NFR-RKG-REL-001#9 | normative item 9 recovery | TEST-RKG-INDEX-JOB-CLI-001; TEST-RKG-CONVERSATION-STATE-001 | passed |
| NFR-RKG-REL-001#10 | normative item 10 history window | TEST-RKG-GROUNDED-QA-001; TEST-RKG-CONVERSATION-API-001 | passed |
| NFR-RKG-REL-001#11 | normative item 11 LLM turn budgets | TEST-RKG-LLM-LIMITS | not_run |

REL items 1–10 stay `passed` on the revision-1 pytest output only. Item 11
stays `not_run`.

## NFR-RKG-UX-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-UX-001#1 | normative item 1 primary flow | not_run | not_run |
| NFR-RKG-UX-001#2 | normative item 2 accessibility | not_run | not_run |
| NFR-RKG-UX-001#3 | normative item 3 contrast and motion | TEST-RKG-WCAG-CONTRAST-002 | not_run |
| NFR-RKG-UX-001#4 | normative item 4 responsive | not_run | not_run |
| NFR-RKG-UX-001#5 | normative item 5 safe rendering | TEST-RKG-CONVERSATION-API-001 | not_run |
| NFR-RKG-UX-001#6 | normative item 6 typography | not_run | not_run |
| NFR-RKG-UX-001#7 | normative item 7 announcements and focus | not_run | not_run |
| NFR-RKG-UX-001#8 | normative item 8 lifecycle safety | TEST-RKG-UI-REPO-MGMT-MOCK-001 | not_run |

Item 5 is `not_run` because revision 1 marked it `passed` from the frontend
conversation page test. Item 8 stays `not_run`.

## NFR-RKG-EXT-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-EXT-001#req-1 | normative requirement 1 LanguageAdapter | not_run | not_run |
| NFR-RKG-EXT-001#req-2 | normative requirement 2 FrameworkAdapter | not_run | not_run |
| NFR-RKG-EXT-001#req-3 | normative requirement 3 immutable manifest / FactBatch | not_run | not_run |
| NFR-RKG-EXT-001#req-4 | normative requirement 4 registry, no adapter branch | not_run | not_run |
| NFR-RKG-EXT-001#req-5 | normative requirement 5 no schema/API change to add adapter | not_run | not_run |
| NFR-RKG-EXT-001#req-6 | normative requirement 6 shared conformance suite | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#req-7 | normative requirement 7 first adapter set is not core | not_run | not_run |
| NFR-RKG-EXT-001#req-8 | normative requirement 8 LLM not normative graph author | not_run | not_run |
| NFR-RKG-EXT-001#acc-1 | acceptance item 1 comparison revision | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#acc-2 | acceptance item 2 TEST-RKG-ADAPTER-CONFORMANCE | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#acc-3 | acceptance item 3 pass_rate 100% | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#acc-4 | acceptance item 4 allowlisted diff | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#acc-5 | acceptance item 5 static check | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |
| NFR-RKG-EXT-001#acc-6 | acceptance item 6 evidence contents | TEST-RKG-ADAPTER-CONFORMANCE-r3 | not_run |

Acceptance item 3 stays `not_run`. `pass_rate` was not measured. Historical
fixture `pass_rate` 1.0 in `TEST-RKG-ADAPTER-CONFORMANCE-r3` is not applied to
TASK-RKG-042..047.

## Adapters TASK-RKG-042..047

`REV-RKG-STACK-SUPPORT-001` revision 2 withholds deep-support. Flask stays
`DETECTED_ONLY`. Conformance figure for TASK-RKG-042..047: **not_run**. It is
not 100%.

| Task | Review statement | Conformance figure |
| --- | --- | --- |
| TASK-RKG-042 | focused rows; no conformance `pass_rate` | not_run |
| TASK-RKG-043 | does not assert `exposes==[]` | not_run |
| TASK-RKG-044 | does not assert AC-RKG-007 `rule_id` and validate-before-publish | not_run |
| TASK-RKG-045 | does not assert AC-RKG-003 import edges | not_run |
| TASK-RKG-046 | null `rule_id` and `start_line`; census skips `file_path`; `validate_fact_batch` only rejects a non-relative entity path | not_run |
| TASK-RKG-047 | capability `DETECTED_ONLY` on every run | not_run |
