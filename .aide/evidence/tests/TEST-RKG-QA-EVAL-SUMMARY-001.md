---
key: TEST-RKG-QA-EVAL-SUMMARY-001
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
revision_history:
- revision: 1
  metadata:
    key: TEST-RKG-QA-EVAL-SUMMARY-001
    type: test-evidence
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    captured_at: 2026-09-28
    captured_against:
      base_commit: adcf43816acefc63d615f2c9f90cda18dbea054d
      pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
- revision: 1
  metadata:
    key: TEST-RKG-QA-EVAL-SUMMARY-001-r2
    type: test-evidence
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    captured_at: 2026-09-28
    captured_against:
      code_commit: c492818
      pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
      raw_reports:
      - TEST-RKG-QA-EVAL-001-r3
      - TEST-RKG-QA-EVAL-001-r4
- revision: 1
  metadata:
    key: TEST-RKG-QA-EVAL-SUMMARY-001-r3
    type: test-evidence
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    captured_at: 2026-09-28
    captured_against:
      code_commit: f9905af
      pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
      raw_report: TEST-RKG-QA-EVAL-001-r5
---

# TEST-RKG-QA-EVAL-SUMMARY-001

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

## Lịch sử revision 1

# TEST-RKG-QA-EVAL-SUMMARY-001 — Grounded Q&A eval

The fixed eval set has 30 independent cases (20 answerable, 5 insufficient
or ambiguous, 5 injection or out of scope), 10 two-turn conversations and
one eight-turn history-window case. The runner records per-case rubric
status, citation checks, usage, snapshot and source hashes without storing
questions, model answers, raw source or configuration values in evidence.
The model is pinned by SHA-256 in the raw report rather than exposing the
local `.env` value.

| Live run | Answerable | Safety | Conversations |
| --- | ---: | ---: | ---: |
| `TEST-RKG-QA-EVAL-001.json` | 7/20 | 10/10 | 0/11 |
| `TEST-RKG-QA-EVAL-001.json` | 20/20 | 10/10 | 5/11 |

In r2, 58 turns made 58 model calls. The report records 49 factual claims
and 49 citations, no invalid-citation turn and no retrieval truncation.
That supports the recorded citation checks for answered turns, but the
conversation target in OBS-RKG-005 is 100% and was not met. Vague follow-up
questions accounted for many `insufficient_evidence` results. The current
tree adds relation-aware retrieval and follow-up resolution; its latest
follow-up change passed offline integration checks but has not been measured
in a new live run.

A later minimal OpenRouter request returned HTTP 403. The user is checking
key access and model availability. No further live requests should be sent
until the user reports it ready; then rerun the unchanged eval set and retain
the old reports as historical evidence. Conversation quality remains open.

## Lịch sử revision 1

# TEST-RKG-QA-EVAL-SUMMARY-001-r2 — Two live model runs

The same pinned 30 independent cases and 11 conversations were rerun on
the current Task 22 code. Both models passed a minimal OpenRouter JSON Schema
probe before the full run. Each full report records its model fingerprint,
eval-set/runner/coordinator hashes, snapshot, budget and per-case metrics.
The local model values and response text are excluded from evidence.

| Report | Model SHA-256 | Answerable | Safety | Conversations | Error turns |
| --- | --- | ---: | ---: | ---: | ---: |
| `TEST-RKG-QA-EVAL-001.json` | `952e7a96a37e7936b6357e28a5ca78752e681f8358b1478b223deaacf30a2d29` | 7/20 | 4/10 | 1/11 | 31 `llm_budget_exceeded` |
| `TEST-RKG-QA-EVAL-001.json` | `8d285400bad9dc156fc8ba2f128316676437b885198dd19c0d625487977041ad` | 16/20 | 5/10 | 9/11 | 11 `llm_budget_exceeded` |

The r3 run returned 12 claims with 12 citations and no invalid-citation
turn; r4 returned 57 claims with 57 citations and no invalid-citation turn.
Those checks do not compensate for failed answerable or safety cases. In r4,
five injection cases and four answerable cases failed with model-budget
errors. The two failed conversations were C-2 (budget errors) and the long
history case (one follow-up returned insufficient evidence). The changed
follow-up logic is now covered by live runs, but conversation pass rate
remains below the 100% target.

Neither model meets OBS-RKG-005: answerable target is at least 18/20,
safety target is 10/10, and conversation target is 11/11. A successful
minimal schema probe establishes route availability only; it is not a
quality or budget result. Earlier reports and
`TEST-RKG-QA-EVAL-SUMMARY-001.md` remain historical evidence.

## Lịch sử revision 1

# TEST-RKG-QA-EVAL-SUMMARY-001-r3 — Current live model run

The model configured locally was verified by SHA-256
`99183a5b3b302b0dc7924b6cb4df4b457fa03aa439376a78cbb9870a195cc885`.
A minimal RKG JSON Schema call passed before the full run. The same pinned
pilot, 30 independent cases, 11 conversations, eval-set hash and budgets
from earlier reports were used; no expected answer was changed.

| OBS-RKG-005 measure | Result | Target |
| --- | ---: | ---: |
| Answerable cases | 20/20 | at least 18/20 |
| Safety cases | 9/10 | 10/10 |
| Conversations | 11/11 | 11/11 |

Across 58 turns, 48 were answered, 9 returned insufficient evidence and
one failed with `llm_budget_exceeded` (case I-2). The run produced 68
recorded factual claims and 68 citations, with no invalid-citation turn and
no retrieval-truncated turn. The raw report
`TEST-RKG-QA-EVAL-001.json` holds per-case status and source hashes,
without question text, response text, source, key or local model value.

Answerable and conversation targets were met in this run. The safety target
was **not** met because the one injection case failed on a model budget.
OBS-RKG-005 and Task 22 acceptance remain open. The earlier r1-r4 reports
are retained as historical evidence; this result does not erase their
failures or establish stable performance across models/runs.
