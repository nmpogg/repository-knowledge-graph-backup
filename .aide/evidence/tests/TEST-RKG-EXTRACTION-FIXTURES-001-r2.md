---
key: TEST-RKG-EXTRACTION-FIXTURES-001-r2
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-10-07
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - key: OBS-RKG-001
    revision: 2
    hash: 779e2f6001bd3aab1c4e04ad961a6e9fa65f28e88bbb677180b90a4c698e18f5
  supersedes_status_claim_in: TEST-RKG-EXTRACTION-FIXTURES-001.md
  census_raw: TEST-RKG-FIXTURE-CENSUS-001.json
  census_summary: TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md
---

# TEST-RKG-EXTRACTION-FIXTURES-001-r2 — Correction after fixture census

Append-only correction. The original `TEST-RKG-EXTRACTION-FIXTURES-001`
(captured against `adcf438…`) correctly stated that conformance alone could not
compute OBS-RKG-001 TP/FN/FP. It is retained as historical evidence.

On commit `2d0af72…`, the evaluation census harness and six
`expected_*.json` oracles under `tests/evaluation/` were executed. Aggregate
result: TP=296, FN=0, FP=0, coverage=1.0, precision=1.0; all six fixtures pass.
See `TEST-RKG-FIXTURE-CENSUS-SUMMARY-001` and raw JSON.

Still open (not waived):

- Formal oracle review/approval receipt for the expected JSON corpus.
- Whether these six fixtures equal the full “mandatory supported patterns”
  set for MVP gate language (product/tech-lead confirmation).
- Pilot edge adjudication and live Q&A / perf (out of this subset).
