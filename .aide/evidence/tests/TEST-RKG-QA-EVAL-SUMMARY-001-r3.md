---
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
source_note: Split from combined TEST-RKG-QA-EVAL-SUMMARY-001.md; that file remains historical.
---

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
