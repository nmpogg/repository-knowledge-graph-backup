---
key: TEST-RKG-EXTRACTION-FIXTURES-001-r3
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
  prior_notes:
  - TEST-RKG-EXTRACTION-FIXTURES-001-r2.md
  oracle_receipt: RCPT-RKG-EVAL-ORACLE-001
  oracle_review: REV-RKG-EVAL-ORACLE-001
---

# TEST-RKG-EXTRACTION-FIXTURES-001-r3 — Mandatory MVP fixture scope

Append-only scope note for KPI-RKG-001 / OBS-RKG-001 gate language. Does not
waive KPI/NFR, close a gate, or assert Product Owner sign-off.

## Measured corpus (in scope for census harness)

| Fixture rel path | Oracle | Adapter stack (census method) | In MVP census |
| --- | --- | --- | --- |
| `repo-test/rkg-fixture-bullmq-worker` | `expected_bullmq.json` | TypeScript + BullMQ | yes |
| `repo-test/rkg-fixture-go-event-worker` | `expected_go.json` | Go + kafka-go + pgx | yes |
| `repo-test/rkg-fixture-nuxt4` | `expected_nuxt.json` | Vue + TypeScript + Nuxt | yes |
| `repo-test/rkg-fixture-react-ts` | `expected_react_ts.json` | TypeScript + React Router | yes |
| `repo-test/soopi` | `expected_soopi.json` | Python + FastAPI + SQLAlchemy (+ messaging) | yes |
| `repo-test/rkg-fixture-spring-orders` | `expected_spring.json` | Java + Spring + JPA + Spring Kafka | yes |

Oracle SHA-256 pins: `RCPT-RKG-EVAL-ORACLE-001` and
`TEST-RKG-FIXTURE-CENSUS-001.json` → `captured_against.oracle_files`.

## Not in measured corpus (explicit out)

| Item | Status | Impact on KPI-001 |
| --- | --- | --- |
| `repo-test/06-polyglot-monorepo.md` → future `rkg-fixture-polyglot-commerce` | **Not created**; no `tests/evaluation/expected_polyglot*.json`; prerequisite doc only | **Out** — multi-root / cross-service linker cases are not covered by current six-fixture census |
| Sibling `../pilot_fastapi` | Unavailable on this host; separate OBS-002 exercise | **Out** of fixture census (pilot review pending owner) |
| Conformance-only synthetic adapter fixture | Covered by `TEST-RKG-ADAPTER-CONFORMANCE`, not census oracles | **Out** of TP/FN/FP census |

## Mandatory MVP set — agent assessment (needs Tech Lead confirm)

**Measured:** all six per-stack golden fixtures that have census oracles today pass
at 100% coverage/precision on commit `2d0af72…` (see
`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001`).

**Not confirmed as complete MVP mandatory set:**

- Polyglot monorepo (prompt `06`) is documented as a **follow-on** integration
  corpus (multi app root, post-merge linker). It is **not** included in the six
  oracles and **must not** be assumed covered until a fixture, oracle, and census
  test exist.
- REG-ADAPTER-001 lists additional profiles (e.g. Flask detected-only); absence
  from census does not imply waiver — only that they are not in this oracle bundle.

**Gate language:** KPI-RKG-001 numeric targets are **met on the six-fixture corpus**
but **owner-reviewed oracles** (`RCPT-RKG-EVAL-ORACLE-001` still `pending`) and
**explicit Tech Lead confirmation** that six fixtures = full MVP mandatory patterns
(or a documented exception list) are still required before treating KPI-001 as closed.

## Oracle review receipt

- Review packet: `REV-RKG-EVAL-ORACLE-001`
- Receipt (pending sign-off): `RCPT-RKG-EVAL-ORACLE-001`
- No `approval-*.yaml` sign-off recorded for oracles in this revision.
