---
key: TEST-RKG-FLASK-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-047
captured_at: 2026-10-08
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 17 }
  - { key: CMP-RKG-ANALYZER, revision: 14 }
  - { key: STORY-RKG-025, revision: 1 }
  - { key: TASK-RKG-047, revision: 2 }
  - { key: PLAN-TASK-RKG-047, revision: 1 }
---

# TEST-RKG-FLASK-001

Current-tree verification for the Flask framework adapter. Checked against the
working tree on the base commit above. No edits under `src/` in this verify
lát. Plan: [`PLAN-TASK-RKG-047.md`](../plans/PLAN-TASK-RKG-047.md). Diary:
[`DIARY-TASK-RKG-047.md`](../diaries/DIARY-TASK-RKG-047.md).

The task under-test paragraph matches the suite: three tests on temporary
fixtures, no repo-test oracle, and no census json. Contract rows below follow
the asserts. AC-RKG-004 in this lát is method, path, and `handled_by`. It is
narrower than the FastAPI given text (nested router, multi-method route,
trailing slash, path param, registration chain, duplicate method/path kept
apart by chain).

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_flask_framework.py -v` | 3 passed |

`DETECTED_ONLY` is asserted on every `_run`: the capability set is exactly
`SupportState.DETECTED_ONLY`. The one-entrypoint case also asserts technology
state `DetectionState.DETECTED_ONLY` and empty `adapter_ids`.

## Contract rows (FR-RKG-002)

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-004 | `test_blueprint_route_add_url_rule_and_plain_callable`: Endpoint method and path are exactly `GET /health`, `GET /ping`, and `POST /v1/items`. `handled_by` targets are exactly `routes_file.create_item`, `web.health`, and `web.ping`. `routes_file.not_routed` and `service.idle` are absent from `handled_by` and remain Callables. `web.moving` remains a Callable and no Endpoint qualified name contains `moving`. One blueprint prefix join is the path `/v1/items`. Trailing-slash inventory, multi-prefix routes, multi-method routes, path params, and registration-chain completeness are not asserted |
| AC-RKG-005 | Same test: `depends_on` from the `/v1/items` Endpoint to `routes_file.require_token`. Parameter defaults, annotations, sub-dependency functions, and a check that the dependency is absent from `calls` are not asserted |
| AC-RKG-006 | Same test: at least one `flask_route_dynamic` diagnostic on relative `web.py` with a line, no backslash, and a path that does not start with `/`; diagnostic messages do not contain `moving`; no Endpoint for that dynamic route. `test_local_flask_module_does_not_become_an_endpoint`: a local `flask` module yields no Endpoint. Instance or self dispatch, star import, and duplicate binding are not asserted. The diagnostic code is present; the suite does not assert explanatory wording beyond that code and the path checks |
| AC-RKG-048 | Same blueprint test: `calls` include `routes_file.create_item` → `service.RoomBook.create`, `service.RoomBook.create` → `service.helper`, `routes_file.not_routed` → `service.RoomBook.create`, and `service.idle` → `service.helper`. Call-site evidence, alias, `await`, constructor calls, module-level calls, shadowed targets, and unresolved targets are not asserted |

## What this verify asserted

| Claim | Covered by |
| --- | --- |
| Endpoint method and path, `handled_by`, unregistered callables left off the handler set, dynamic route left off the Endpoint set | `test_blueprint_route_add_url_rule_and_plain_callable` |
| One `depends_on` edge to the route decorator callable | same test |
| Four `calls` edges through the routed handler, the class method, and two unregistered callables | same test |
| `flask_route_dynamic` on a relative path | same test |
| One entrypoint `web:app` selected with status `ready`; Flask technology `DETECTED_ONLY` | `test_one_entrypoint_is_selected_and_many_require_a_choice` |
| Two entrypoints return `app_selection_required` with code `app_selection_required` and candidates `other:app`, `web:app`; an unchosen run has no Endpoint and diagnostic `flask_app_ambiguous`; choosing `web:app` yields path `/only` | same test |
| Local module named `flask` yields no Endpoint | `test_local_flask_module_does_not_become_an_endpoint` |
| Capability `DETECTED_ONLY` and framework conformance pass rate 1.0 | every `_run` |

## Not asserted this turn

| Contract ID | Note |
| --- | --- |
| AC-RKG-003 | Import statements appear in the temporary fixtures. The suite does not assert import edges |
| AC-RKG-007 | `validate_fact_batch` runs inside `_run`. The tests do not assert evidence locations or rule ids |
| AC-RKG-035 | No syntax-error sibling in `test_flask_framework.py` |
| Registration-chain completeness | Not asserted |
| Trailing-slash inventory | Not asserted |
| Multi-prefix routes | Not asserted. The suite checks one prefix join (`/v1` + `/items`) |

There is no Flask census row. This record does not link a census summary.

Deep-support promotion remains open; TASK-RKG-047 stays `in_progress`.
