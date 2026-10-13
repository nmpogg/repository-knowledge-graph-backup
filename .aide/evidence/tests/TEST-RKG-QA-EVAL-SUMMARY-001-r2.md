---
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
source_note: Split from combined TEST-RKG-QA-EVAL-SUMMARY-001.md; that file remains historical.
---

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
