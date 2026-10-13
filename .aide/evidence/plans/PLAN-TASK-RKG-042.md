---
key: PLAN-TASK-RKG-042
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-042
revision: 1
plan_date: '2026-10-06'
provenance: tdd-red-phase
captured_against:
  code_tree: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  context: CTX-TASK-RKG-042.yaml
verification_targets:
- path: tests/conformance/test_typescript_language.py
  tests:
  - test_named_default_namespace_alias_and_path_alias_imports
  - test_orders_page_call_chain_to_http_client
  - test_vite_configuration_keys_and_inventory_origin
  - test_secret_sentinel_is_not_persisted
  - test_dynamic_import_is_not_guessed
  - test_dynamic_url_is_not_guessed
  - test_ambiguous_binding_is_not_guessed
  - test_shadowed_fetch_is_not_http_technology
  - test_syntax_error_is_isolated_with_relative_path
  ac:
  - AC-RKG-003
  - AC-RKG-006
  - AC-RKG-007
  - AC-RKG-035
  - AC-RKG-048
- path: tests/conformance/test_react_router_framework.py
  tests:
  - test_static_route_registration_paths
  - test_dynamic_conditional_route_is_diagnostic
  ac:
  - AC-RKG-006
  - AC-RKG-007
  note: UI route entity type blocked by OQ-RKG-007; path inventory only
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-042
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-042
    captured_at: 2026-10-06
  record: 'TDD RED: focused conformance tests only; no adapter under src/.'
---

# PLAN-TASK-RKG-042

TDD RED for TypeScript language and React Router framework adapters. Oracle:
`repo-test/rkg-fixture-react-ts` README inventory (semantic names/paths only).

## Thứ tự (RED → GREEN)

1. **DoR** — TASK/CTX/PLAN; REG-ADAPTER-001 draft for `rkg.typescript` and
   `rkg.react-router`; OQ-RKG-007 if UI route entity type unresolved.
2. **RED language** — `tests/conformance/test_typescript_language.py` only.
   Imports future `rkg.adapters.typescript_language` (absent → ImportError RED).
   Map AC-RKG-003/006/007/035/048 to focused cases. **No adapter under src/.**
3. **RED framework** — `tests/conformance/test_react_router_framework.py` only.
   Imports future `rkg.adapters.react_router_framework`. Assert static path
   inventory; negative dynamic route → diagnostic. Do not coerce UI paths to
   FastAPI HTTP `Endpoint`.
4. **GREEN (later task/revision)** — real parser/extractor modules under src/;
   conformance pass_rate 100%; deep-support review before claiming deep-supported.
5. **Golden full fixture (later)** — optional allowlisted index of
   `repo-test/rkg-fixture-react-ts`; subset inventory asserts; no entity hash IDs.

## Files this revision creates

| Path | Role |
| --- | --- |
| `tests/conformance/test_typescript_language.py` | Focused RED language tests |
| `tests/conformance/test_react_router_framework.py` | Focused RED framework tests |
| `.aide/registry/REG-ADAPTER-001.md` | Draft profiles + pattern tables |
| `.aide/.../OQ-RKG-007.md` | UI route entity type |

## Không làm

- Real TypeScript/TSX parse or React Router extract.
- Evaluation / KPI census / EVAL-RKG-QA / pilot Q&A.
- Polyglot monorepo, Java, Go, Nuxt, BullMQ adapters.
- Mark task `done` or claim deep-supported.
- Commit unless explicitly requested.
