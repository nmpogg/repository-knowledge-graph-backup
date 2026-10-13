---
key: TEST-RKG-FIXTURE-CENSUS-SUMMARY-001
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
  raw_report: TEST-RKG-FIXTURE-CENSUS-001.json
  plan: PLAN-TASK-RKG-022-r4.md
---

# TEST-RKG-FIXTURE-CENSUS-SUMMARY-001 — Fixture census (OBS-RKG-001)

Subset eval (operator option a): no pilot. Runner:
`pytest tests/evaluation/test_*_census.py -v` → **12 passed**.
Raw counts in `TEST-RKG-FIXTURE-CENSUS-001.json` (relative fixture paths,
oracle/tree hashes, method string; no absolute host paths, secrets, or source).

| Fixture | Method | TP | FN | FP | Coverage | Precision | Outcome |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| rkg-fixture-bullmq-worker | typescript+bullmq | 27 | 0 | 0 | 1.0 | 1.0 | pass |
| rkg-fixture-go-event-worker | go+kafka-go+pgx | 41 | 0 | 0 | 1.0 | 1.0 | pass |
| rkg-fixture-nuxt4 | vue+typescript+nuxt | 37 | 0 | 0 | 1.0 | 1.0 | pass |
| rkg-fixture-react-ts | typescript+react-router | 34 | 0 | 0 | 1.0 | 1.0 | pass |
| soopi | python+fastapi+sqlalchemy | 106 | 0 | 0 | 1.0 | 1.0 | pass |
| rkg-fixture-spring-orders | java+spring+jpa+spring-kafka | 51 | 0 | 0 | 1.0 | 1.0 | pass |
| **Aggregate** | 6 fixtures | **296** | **0** | **0** | **1.0** | **1.0** | **pass** |

## Method / version / omissions

- Harness: `tests/evaluation/census_support.py` SHA-256 pinned in raw report.
- Oracles: `tests/evaluation/expected_*.json` SHA-256 pinned in raw report.
- Canonical compare drops generated IDs/timestamps; matches type, identity,
  required attributes, relationship direction, `rule_id`, relative evidence.
- Some oracles set `allow_unlisted_actual` (see raw per fixture); FP then
  excludes unlisted actuals and counts only unexpected/prohibited/secret hits.
- Oracle **review receipt** is not recorded in this evidence; numbers are
  measured on current tree only.
- Sibling `pilot_fastapi` was **not** part of this census.

## Acceptance note

OBS-RKG-001 / KPI-RKG-001 targets (coverage 100%, precision 100%, no mandatory
fixture fail) are **met on this six-fixture corpus** at commit above. This does
not waive other open findings, close a gate, or claim owner-reviewed oracles.
Prior `TEST-RKG-EXTRACTION-FIXTURES-001` remains historical; see
`TEST-RKG-EXTRACTION-FIXTURES-001-r2`.
