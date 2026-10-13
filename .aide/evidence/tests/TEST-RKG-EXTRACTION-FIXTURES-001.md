---
key: TEST-RKG-EXTRACTION-FIXTURES-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  base_commit: adcf43816acefc63d615f2c9f90cda18dbea054d
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
---

# TEST-RKG-EXTRACTION-FIXTURES-001 — Extraction fixture status

`pytest tests/conformance -q` passed 36 tests on the Task 22 working tree.
The focused adapter fixture passed 2 tests and its 25 historical contract
cases passed. `TEST-RKG-ADAPTER-CONFORMANCE.json` pins the current code
hashes, fixture revision, diff allowlist and static-check results.

The conformance suite exercises supported and negative extraction patterns,
but it does not enumerate every expected canonical entity and edge with
required attributes, rule and evidence location in reviewed expected JSON.
It therefore cannot calculate the TP/FN/FP census required by OBS-RKG-001.
KPI-RKG-001 coverage and precision remain **unmeasured**, rather than 100%.
The pilot's 160 sampled edges in `TEST-RKG-PILOT-REVIEW-001.json` are a
separate precision exercise and cannot substitute for this fixture census.

To close this finding, add a reviewed canonical expected-fact corpus and
comparison report for every mandatory supported pattern, including explicit
negative expectations and any approved allowlist.
