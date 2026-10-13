---
key: TEST-RKG-BULLMQ-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-044
captured_at: 2026-10-07
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 12 }
  - { key: STORY-RKG-028, revision: 1 }
  - { key: TASK-RKG-044, revision: 5 }
  - { key: PLAN-TASK-RKG-044, revision: 1 }
---

# TEST-RKG-BULLMQ-001

Current-tree verification for BullMQ messaging adapter (`rkg.bullmq`). Checked
against the working tree on base commit above. No adapter code changes in this
verify lát; no edits under `src/rkg/adapters/**`. Plan:
[`PLAN-TASK-RKG-044.md`](../plans/PLAN-TASK-RKG-044.md). Diary append:
[`DIARY-TASK-RKG-044-r2.md`](../diaries/DIARY-TASK-RKG-044-r2.md).

Verify path is **census-only**: `tests/evaluation/test_bullmq_census.py` /
`expected_bullmq.json`. There is no separate BullMQ conformance suite in tree;
this evidence does not claim one.

Corpus context (bullmq row):
[`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md`](TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md)
— `rkg-fixture-bullmq-worker` / typescript+bullmq / 27 TP / 0 FN / 0 FP /
coverage 1.0 / precision 1.0 / pass.

| Check | Result |
| --- | --- |
| `pytest tests/evaluation/test_bullmq_census.py -v` | 2 passed |

## Contract rows (FR-RKG-002)

Map carefully to what the census oracle / harness actually assert. Do not treat
census pass as a full dedicated AC suite.

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-015 | Census oracle inventory: static-name `MessageChannel` entities; curated `publishes` / `consumes` edges; prohibited dynamic-queue publish, reassigned-worker consume, unscoped/`LocalPublisher` publish, shadowed Queue/Worker publish, and cleanup-as-HTTP `Endpoint`. Oracle notes: no Redis URL/connection or payload as graph facts. `channel_kind=queue` is REG/`STORY-RKG-028` contract text — **not** in oracle `required_attributes` this turn |
| AC-RKG-006 | Corpus-level only: oracle `prohibited` rows above block guessed BullMQ channel edges for dynamic / shadowed / unscoped / reassigned patterns. No dedicated `TEST-RKG-NO-GUESS` BullMQ conformance suite |
| AC-RKG-007 | Corpus-level only: curated entities/edges carry relative `file_path` evidence in the oracle; census compare matches that inventory. Oracle sets `rule_id: null` where README does not name a versioned rule — full AC-007 rule_id + validate-before-publish suite **not** asserted here |
| NFR-RKG-SEC-001 | Secret sentinel must not appear in census output / prohibited text (`test_bullmq_census.py` + oracle) |

## What this verify asserted

| Claim | Covered by |
| --- | --- |
| Oracle loads; fixture id + MessageChannel `order-processing` present | `test_expected_oracle_loads` |
| Census vs `expected_bullmq.json` outcome pass, coverage 1.0, precision 1.0 | `test_bullmq_census_matches_expected` |
| Secret sentinel and absolute fixture root absent from captured report text | same test assertions |
| Aggregate corpus row (27/0/0) | linked summary only — not re-run / not rewritten this lát |

Deep-support promotion remains open; TASK-RKG-044 stays `in_progress`.
