---
key: TEST-RKG-PILOT-REVIEW-SUMMARY-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  base_commit: adcf43816acefc63d615f2c9f90cda18dbea054d
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
---

# TEST-RKG-PILOT-REVIEW-SUMMARY-001 — Pilot edge review

The pinned sibling FastAPI pilot is a controlled synthetic corpus with 23
source files. The scan considered 21 files, parsed 20, and produced 313
entities and 550 edges with `succeeded_with_warnings`. Its unresolved
diagnostics were 185 calls, 132 imports, 2 SQLAlchemy models, 1 base and
1 dynamic route. These are omissions and are not counted as reviewed TP.

`TEST-RKG-PILOT-REVIEW-001.json` records a deterministic seed (220026),
stable edge IDs, source evidence locations, populations and samples. The
sampling rule is 30 each for import, call and DI, and 10 each for DB maps,
reads, writes, event publish, consume, config and implements. This is 160
samples across 10 groups. The runner checked each sampled evidence site
against parsed source syntax and provisionally labeled all 160 TP.

Every sample still has `owner_adjudication: pending`. OBS-RKG-002 requires
reviewers to open source context and adjudicate TP/FP; the AST check alone
does not establish pilot precision. Group precision and KPI-RKG-002 therefore
remain **pending**, including the 95% target. The raw sheet is ready for
Product Owner and Tech Lead review without changing the sample or seed.
