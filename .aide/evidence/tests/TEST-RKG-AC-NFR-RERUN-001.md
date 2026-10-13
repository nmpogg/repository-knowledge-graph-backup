---
key: TEST-RKG-AC-NFR-RERUN-001
type: test-evidence
group: evidence
system: SYS-RKG
status: recorded
revision: 1
captured_at: 2026-10-08
captured_against:
  code_commit: 4c6ab37789eda0cd820c86313bef1e71359eacb0
  working_tree: dirty
---

# TEST-RKG-AC-NFR-RERUN-001 — AC/NFR re-run matrix

Append-only record for the current working tree. Does not edit historical test
evidence. Does not mark a story, task, epic, or gate done. Does not sign an
approval. Status values are only `passed`, `failed`, and `not_run`. Skipped
tests stay `not_run`.

## Tree

`git rev-parse HEAD` = `4c6ab37789eda0cd820c86313bef1e71359eacb0`. Working tree
was dirty. Uncommitted product diffs: `frontend/src/components/graph/KnowledgeGraph.tsx`,
`frontend/src/components/graph/graphLayout.ts`,
`frontend/src/components/graph/graphLayout.test.ts`, deleted `tests/evals/.gitkeep`.
Pre-existing untracked findings and `REV-RKG-STACK-SUPPORT-001.yaml` were not
edited. This file is the new test record.

## Commands this round

| Suite | Command | Result |
| --- | --- | --- |
| PY | `uv run pytest tests -q --tb=no` | 246 passed, 7 skipped, 0 failed |
| PY-RS | `uv run pytest tests -q -rs --tb=no` | 246 passed, 7 skipped, 0 failed |
| RUFF | `uv run ruff check src tests` | failed — 17 E501 |
| FE | `npm test` in `frontend` | 13 files, 77 passed, 0 failed |
| TSC | `npx tsc -b --pretty false` in `frontend` | passed (exit 0) |

Skipped (`not_run`, not passed):

| Location | Reason |
| --- | --- |
| `tests/integration/test_core_api.py:699` | creating symlinks is not permitted on this host |
| `tests/unit/test_local_source.py:164` | creating symlinks is not permitted on this host |
| `tests/integration/test_openrouter_live.py:12` | OpenRouter credential unavailable |
| `tests/integration/test_grounded_qa_live.py:16` | OpenRouter credential unavailable |
| `tests/integration/test_grounded_qa_live.py:60` | OpenRouter credential unavailable |
| `tests/integration/test_pilot_corpus.py` (2) | sibling pilot repository is unavailable |

Not invoked: pilot benchmark runner, pilot Q&A eval runner, WCAG contrast
recalculation, adapter `pass_rate` recount, static core-branch check, allowlist
diff. Analyzed-repository source was not executed. Pilot tests skipped before
opening a sibling repository.

Counts for commands above: passed suites PY, PY-RS, FE, TSC; failed suite RUFF;
skipped pytest cases 7 `not_run`. RUFF is not an acceptance suite in the matrix;
it does not flip AC rows to `failed`.

`rerun` below is this round only. `evidence` is an existing test-evidence key
that names the AC or the `validated_by` id. `not_run` in the evidence column
means no such file was found. A historical file that says the check was not
executed, or a live/benchmark run that this round did not repeat, stays
`not_run` even if PY passed other tests.

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
| AC-RKG-072 | TEST-RKG-REPOSITORY-ISOLATION | TEST-RKG-CORE-API-001 | passed |
| AC-RKG-072 | TEST-RKG-REPOSITORY-MANAGEMENT-A11Y | not_run | not_run |

AC-RKG-039: benchmark runner was not started. `TEST-RKG-PERF-SUMMARY-001` already
records context p95 failing the threshold on some historical runs and an
unconfirmed reference host. That historical result is not a this-round fail
or pass.

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

AC-RKG-035 stays `not_run`: `TEST-RKG-JAVA-SPRING-001`, `TEST-RKG-GO-KAFKA-PGX-001`,
and `TEST-RKG-FLASK-001` record no syntax-error sibling. Vue syntax coverage is
inside PY and is not promoted to an AC pass. `TEST-RKG-TYPESCRIPT-REACT-ROUTER-001`
names AC-RKG-035 on a call-chain row; that row is not used as syntax evidence.

AC-RKG-003 stays `not_run`: Java, Go, and Flask evidence record import edges not
asserted. Focused-flow, TypeScript, and Vue rows that do assert imports are
inside PY.

AC-RKG-007 stays `not_run`: FastAPI evidence maps `TEST-RKG-EVIDENCE`, and those
tests are inside PY, but BullMQ, Java, Go, and Flask evidence say the full
rule-id / validate-before-publish suite is not asserted. Go revision
`TEST-RKG-GO-KAFKA-PGX-001-r2` records the same gap.

AC-RKG-048 stays `not_run`: no test-evidence key equals `TEST-RKG-CALL-RESOLVE`.
Listed files assert some `calls`. Call-site evidence is recorded as not asserted
on Java, Go, and Flask. The TypeScript file's AC-RKG-048 row is Vite keys and an
origin, so it is not call-resolve evidence.

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
| AC-RKG-073 | TEST-RKG-UI-STRUCTURE | TEST-RKG-UI-STRUCTURE | passed |

AC-RKG-037: `TEST-RKG-GRAPH-READS-001` says the p95 report was not executed.
`TEST-RKG-PERF-SUMMARY-001` holds older latencies. Benchmark not re-run.
AC-RKG-073 re-run command is FE (`structureTree` / `ExplorerPage` tests included).

## FR-RKG-004

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-010 | TEST-RKG-CONTEXT | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | passed |
| AC-RKG-062 | TEST-RKG-CONTEXT-BENCHMARK | TEST-RKG-GRAPH-READS-001; TEST-RKG-CORE-API-001 | not_run |

AC-RKG-062: both files say the p95 benchmark was not executed there.
`TEST-RKG-PERF-SUMMARY-001` is the historical context latency record and was
not re-run.

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
| AC-RKG-046 | TEST-RKG-CONVERSATION-A11Y | TEST-RKG-CONVERSATION-API-001 | passed |
| AC-RKG-059 | TEST-RKG-TURN-REQUIRED-FIELDS | TEST-RKG-CONVERSATION-STATE-001 | passed |
| AC-RKG-064 | TEST-RKG-CONVERSATION-REDACTION | TEST-RKG-CONVERSATION-STATE-001 | passed |

AC-RKG-024: live eval runner was not started. Pilot corpus tests skipped.
`TEST-RKG-QA-EVAL-001-r6` is the raw report key inside `TEST-RKG-QA-EVAL-001.json`.
Deterministic service cases named by `TEST-RKG-GROUNDED-QA-001` are inside PY
and are not treated as the eval pass.

AC-RKG-028: live follow-up in `test_grounded_qa_live.py` skipped. Deterministic
follow-up tests are inside PY. Combined status stays `not_run`.

AC-RKG-063: `TEST-RKG-LLM-LIMITS` says the AC is partial. Live provider tests
skipped. Unit/API budget tests are inside PY and are not recorded here as a
completed AC pass.

AC-RKG-046 re-run command is FE (`ConversationPage.test.tsx` included).

## NFR-RKG-PERF-001

Threshold rows. None were re-measured.

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

Item 5 files name `NFR-RKG-SEC-001` for a secret-sentinel check, and conversation
redaction is AC-RKG-064. That slice is inside PY. The item also covers logs,
payloads, and transcripts beyond those asserts, so the item stays `not_run`.
Items 1–4 and 6–8 have no test-evidence file that names the item.

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

Item 11 matches AC-RKG-063: partial historical record, live provider `not_run`.

## NFR-RKG-UX-001

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| NFR-RKG-UX-001#1 | normative item 1 primary flow | not_run | not_run |
| NFR-RKG-UX-001#2 | normative item 2 accessibility | not_run | not_run |
| NFR-RKG-UX-001#3 | normative item 3 contrast and motion | TEST-RKG-WCAG-CONTRAST-002 | not_run |
| NFR-RKG-UX-001#4 | normative item 4 responsive | not_run | not_run |
| NFR-RKG-UX-001#5 | normative item 5 safe rendering | TEST-RKG-CONVERSATION-API-001 | passed |
| NFR-RKG-UX-001#6 | normative item 6 typography | not_run | not_run |
| NFR-RKG-UX-001#7 | normative item 7 announcements and focus | not_run | not_run |
| NFR-RKG-UX-001#8 | normative item 8 lifecycle safety | TEST-RKG-UI-REPO-MGMT-MOCK-001 | not_run |

Item 3: contrast file exists; the measurement was not repeated. Reduced motion
is not in that file. Item 5 re-run is FE (escaped markup in `ConversationPage`).
Item 8: mock delete/conflict tests are inside FE; the same file says confirm
dialogs and danger-zone states were not automated, so the item stays `not_run`.

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

`TEST-RKG-ADAPTER-CONFORMANCE-r3` is the key inside `TEST-RKG-ADAPTER-CONFORMANCE.json`.
It records historical `pass_rate` 1.0 on fixture adapters
`rkg.conformance.fixture.language` and `rkg.conformance.fixture.framework`
(`passed_contract_tests` 25 / `total_contract_tests` 25), task `TASK-RKG-022`.
This round did not recount that ratio, did not repeat the static check, and did
not repeat the allowlist diff. PY includes `tests/conformance/test_adapter_conformance.py`
(that module is not in the skip list). That inclusion is not a measured
`pass_rate` and is not applied to TASK-RKG-042..047.

## Adapters TASK-RKG-042..047

Source: `REV-RKG-STACK-SUPPORT-001` revision 2, status closed. Promotion to
deep-supported is withheld for every adapter. Tasks stay in progress.
`reviewed_deep_support` stays false. Flask stays `DETECTED_ONLY`. The review
does not record `TEST-RKG-ADAPTER-CONFORMANCE` `pass_rate` = 100%.

| Task | Review statement | Conformance figure this round |
| --- | --- | --- |
| TASK-RKG-042 | `TEST-RKG-TYPESCRIPT-REACT-ROUTER-001` has focused rows and does not record a conformance `pass_rate` | not_run |
| TASK-RKG-043 | `TEST-RKG-VUE-NUXT-001` does not assert `exposes==[]` in `test_nuxt_framework.py` | not_run |
| TASK-RKG-044 | `TEST-RKG-BULLMQ-001` does not assert the AC-RKG-007 `rule_id` and validate-before-publish suite | not_run |
| TASK-RKG-045 | `TEST-RKG-JAVA-SPRING-001` does not assert AC-RKG-003 import edges | not_run |
| TASK-RKG-046 | `TEST-RKG-GO-KAFKA-PGX-001-r2` records null `rule_id` and `start_line`, census compare that skips `file_path`, a null oracle `rule_id` that is not checked, and `validate_fact_batch` that only rejects a non-relative entity path | not_run |
| TASK-RKG-047 | `TEST-RKG-FLASK-001` records capability `DETECTED_ONLY` on every run | not_run |

Recorded conformance figure for TASK-RKG-042..047: **not_run**. It is not 100%.
Flask capability recorded from existing evidence and the review: **DETECTED_ONLY**.
PY did not change that capability; flask conformance tests are inside the 246
passed and were not scored as contract `pass_rate`.
