---
key: TEST-RKG-TYPESCRIPT-REACT-ROUTER-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-042
captured_at: 2026-10-07
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 10 }
  - { key: STORY-RKG-026, revision: 1 }
  - { key: TASK-RKG-042, revision: 2 }
---

# TEST-RKG-TYPESCRIPT-REACT-ROUTER-001

Current-tree verification for TypeScript language + React Router framework
adapters. Checked against the working tree on base commit above. No adapter
code changes in this verify lát. Plan:
[`PLAN-TASK-RKG-042-r2.md`](../plans/PLAN-TASK-RKG-042-r2.md). Diary append:
[`DIARY-TASK-RKG-042-r4.md`](../diaries/DIARY-TASK-RKG-042-r4.md).

Corpus context (react-ts row):
[`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md`](TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md)
— `rkg-fixture-react-ts` / typescript+react-router / 34 TP / 0 FN / 0 FP /
coverage 1.0 / precision 1.0 / pass.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_typescript_language.py tests/conformance/test_react_router_framework.py -v` | 14 passed |
| `pytest tests/evaluation/test_react_ts_census.py -v` | 2 passed |

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-003 | Named/default/namespace/alias and path-alias `@/` imports resolve; relative `../` imports covered in language conformance |
| AC-RKG-006 | Dynamic import, dynamic URL, ambiguous binding, and shadowed `fetch` produce no guessed facts |
| AC-RKG-007 | Focused facts carry source evidence; syntax-error fixture isolates with a relative path |
| AC-RKG-035 | Call chain `OrdersPage → useOrders → orderApi.listOrders → httpClient.get` asserted in language conformance |
| AC-RKG-048 | Vite keys `VITE_API_BASE_URL` / `VITE_ENABLE_ADMIN` and literal origin `https://inventory.example.test`; secret sentinel not persisted |

## Navigation assert (OQ-RKG-007)

Resolved: static React Router paths are `Endpoint` with `kind=navigation` and
`framework_kind=react-router`, no HTTP method, no repository `exposes`. Dynamic
or conditional route yields a diagnostic. Asserted in
`test_react_router_framework.py` (path inventory via navigation attributes).

Deep-support promotion remains open; TASK-RKG-042 stays `in_progress`.
