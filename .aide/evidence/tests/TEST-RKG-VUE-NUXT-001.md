---
key: TEST-RKG-VUE-NUXT-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-043
captured_at: 2026-10-07
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 11 }
  - { key: STORY-RKG-027, revision: 1 }
  - { key: TASK-RKG-043, revision: 3 }
---

# TEST-RKG-VUE-NUXT-001

Current-tree verification for Vue language + Nuxt framework adapters. Checked
against the working tree on base commit above. No adapter code changes in this
verify lát. Plan:
[`PLAN-TASK-RKG-043.md`](../plans/PLAN-TASK-RKG-043.md). Diary append:
[`DIARY-TASK-RKG-043-r3.md`](../diaries/DIARY-TASK-RKG-043-r3.md).

Corpus context (nuxt4 row):
[`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md`](TEST-RKG-FIXTURE-CENSUS-SUMMARY-001.md)
— `rkg-fixture-nuxt4` / vue+typescript+nuxt / 37 TP / 0 FN / 0 FP /
coverage 1.0 / precision 1.0 / pass.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_vue_language.py tests/conformance/test_nuxt_framework.py -v` | 14 passed |
| `pytest tests/evaluation/test_nuxt_census.py -v` | 2 passed |

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-003 | Explicit relative `.vue` child import resolves; SFC template/script/style stay sections on one SourceUnit |
| AC-RKG-006 | Nuxt `#shared/...` hash alias, shadowed `fetch`, and ambiguous auto-import produce no guessed facts |
| AC-RKG-007 | Focused facts / edges carry source evidence |
| AC-RKG-035 | Syntax-error sibling isolates with a relative path |
| AC-RKG-048 | Unique same-SFC internal `calls` asserted in language conformance |
| NFR-RKG-SEC-001 | Secret sentinel not persisted |
| REG-ADAPTER-001 / rkg.nuxt Configuration | Nuxt `runtimeConfig` / `runtimeDefaults` keys covered as Configuration in framework conformance |

## Navigation assert (OQ-RKG-007)

Product decision (OQ-RKG-007): Nuxt pages are `Endpoint` with `kind=navigation`
and `framework_kind=nuxt`, no HTTP method, no repository `exposes`. Nitro
`server/api` routes remain separate HTTP Endpoints (method+path).

What this verify asserted:

| Claim | Covered by |
| --- | --- |
| `kind=navigation` + page path inventory vs Nitro HTTP method+path inventory | `test_nuxt_framework.py` |
| `framework_kind=nuxt` | census / oracle (`test_nuxt_census.py` / fixture census); not asserted inside `test_nuxt_framework.py` |
| `exposes==[]` | not asserted in `test_nuxt_framework.py` this turn |

Deep-support promotion remains open; TASK-RKG-043 stays `in_progress`.
