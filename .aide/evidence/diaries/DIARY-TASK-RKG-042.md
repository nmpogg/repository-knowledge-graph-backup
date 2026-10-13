---
key: DIARY-TASK-RKG-042
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-042
revision: 1
implementation_window:
  from: '2026-10-06'
  through: '2026-10-06'
provenance: red-phase-tdd
captured_against:
  code_tree: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
---

# DIARY-TASK-RKG-042

## Diễn giải

- 2026-10-06 — DoR: TASK-RKG-042 `in_progress`, CTX/PLAN, REG-ADAPTER-001 r11 draft
  for `rkg.typescript` + `rkg.react-router`, OQ-RKG-007 (UI navigation entity type).
- 2026-10-06 — Focused tests only (no adapter under `src/rkg/adapters/`):
  - `tests/conformance/test_typescript_language.py`
  - `tests/conformance/test_react_router_framework.py`
- 2026-10-06 — Correction: removed mistaken stub modules
  `typescript_language.py` / `react_router_framework.py` from `src/`; tests import
  future production paths so RED = thiếu adapter (`ModuleNotFoundError`).

## Test → AC → README pattern

| Test | AC | README / oracle |
| --- | --- | --- |
| `test_named_default_namespace_alias_and_path_alias_imports` | AC-RKG-003 | named/default/namespace/alias, `../`, `@/` |
| `test_orders_page_call_chain_to_http_client` | AC-RKG-048, AC-RKG-007 | OrdersPage→useOrders→listOrders→get |
| `test_vite_configuration_keys_and_inventory_origin` | (config/HTTP language output) | `VITE_*` keys + inventory origin |
| `test_secret_sentinel_is_not_persisted` | safety | `RKG_TEST_SECRET_DO_NOT_PERSIST` |
| `test_dynamic_import_is_not_guessed` | AC-RKG-006 | `dynamicImport.ts` |
| `test_dynamic_url_is_not_guessed` | AC-RKG-006 | `dynamicUrl.ts` |
| `test_ambiguous_binding_is_not_guessed` | AC-RKG-006 | `ambiguousBinding.ts` |
| `test_shadowed_fetch_is_not_http_technology` | AC-RKG-006 | `shadowedFetch.ts` |
| `test_syntax_error_is_isolated_with_relative_path` | AC-RKG-035 | syntax-error corpus |
| `test_static_route_registration_paths` | AC-RKG-007 (+ inventory) | route chain; not HTTP Endpoint (OQ-007) |
| `test_dynamic_conditional_route_is_diagnostic` | AC-RKG-006 | negative dynamic route |

## Pytest RED proof

Command (from repo root, project venv):

```text
.venv/Scripts/python.exe -m pytest tests/conformance/test_typescript_language.py tests/conformance/test_react_router_framework.py -q --tb=line
```

Observed after removing src stubs: all oracle tests fail with
`ModuleNotFoundError` / `ImportError` for
`rkg.adapters.typescript_language` or `rkg.adapters.react_router_framework`
(thiếu adapter). Not fixture typos. Valid RED.

## GREEN (append)

- 2026-10-06 — Implemented adapters from fixture README + REG (not tests as oracle):
  - `src/rkg/adapters/typescript_parse.py` (tree-sitter TS/TSX IR)
  - `src/rkg/adapters/typescript_language.py`
  - `src/rkg/adapters/typescript_resolution.py`
  - `src/rkg/adapters/react_router_framework.py`
  - registered in `builtins.py`; deps `tree-sitter`, `tree-sitter-typescript`
- Navigation routes: Endpoint + `framework_kind=react-router`,
  `kind=navigation`, `path`/`route_path`, no HTTP method / no API `exposes`
  (OQ-RKG-007 resolved option 1).
- REG-ADAPTER-001 → revision 12 (implemented, not deep-supported).
- Verification (post-impl only):
  `.venv/Scripts/python.exe -m pytest tests/conformance/test_typescript_language.py tests/conformance/test_react_router_framework.py -q`
  → **11 passed**. Task not marked `done` (deep-support review pending).
- 2026-10-06 — Explorer FE List+Flow (additive): preset `ui_to_api`, navigation
  flow opens `depends_on` for config/external; HTTP Endpoint flow unchanged;
  List copy/page_handler/route_signal; hide API→DB when no data path.

## Không làm

- Claim deep-supported / mark task `done` without review.
- Evaluation / KPI / Q&A eval.
- Full golden index of `repo-test/rkg-fixture-react-ts` (PLAN follow-up).

## Câu hỏi mở

- (none) — OQ-RKG-007 resolved: Endpoint + `kind=navigation` /
  `framework_kind=react-router`.
