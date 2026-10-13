---
key: TEST-RKG-QA-EVAL-SUMMARY-001-r4
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  code_commit: 249684a
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
  raw_report: TEST-RKG-QA-EVAL-001-r6
  coordinator_sha256: pinned-in-raw-report
source_note: Split from combined TEST-RKG-QA-EVAL-SUMMARY-001.md; that file remains historical.
---

# TEST-RKG-QA-EVAL-SUMMARY-001-r4

The grounded planner and edge-selection requests now use the shared
`TurnBudget.max_output_tokens` value of 1,500 tokens per model call, within
the current NFR-RKG-REL-001 limit. The previous per-request caps were 250
and 500. The limits of two model calls, three graph queries and 30 seconds
per turn did not change. This run uses the same pilot digest, eval-set hash,
runner hash and model fingerprint as the prior DeepSeek run, with a new
coordinator hash for the budget change.

| OBS-RKG-005 measure | Previous run r5 | Current run r6 | Target |
| --- | ---: | ---: | ---: |
| Answerable cases | 20/20 | 20/20 | at least 18/20 |
| Safety cases | 9/10 | 10/10 | 10/10 |
| Conversations | 11/11 | 11/11 | 11/11 |
| `llm_budget_exceeded` turns | 1 | 0 | 0 |

The current run had 58 turns: 48 answered and 10 insufficient evidence.
It recorded 68 factual claims and 68 citations, with no invalid-citation
turn and no retrieval truncation. The failed safety case I-2 from r5
passed in r6. `TEST-RKG-QA-EVAL-001.json` holds per-case outcomes and
source hashes without question text, response text, local model value or key.

All recorded OBS-RKG-005 targets are met in this run. This is one live run
on the pinned pilot and model; prior failures remain historical evidence.
Current-tree verification also returned 134 passed, 4 skipped for
`python -m pytest tests -q`; `ruff check src tests` passed. The one pytest
warning was the existing Starlette TestClient deprecation warning.
Task 22 remains in progress because fixture-census, pilot owner review and
performance findings are still open.
