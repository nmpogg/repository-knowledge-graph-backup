---
key: TASK-RKG-047
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-025
status: in_progress
revision: 4
authorization: CR-RKG-029
change_set: CHG-RKG-2026-014
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-004
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-047.yaml
  plan: PLAN-TASK-RKG-047.md
  diary: DIARY-TASK-RKG-047.md
---
# TASK-RKG-047 — Flask static route adapter

Story: STORY-RKG-025. Adapter `rkg.flask` is registered with capability
`DETECTED_ONLY` and `reviewed_deep_support = False`. It is not a reviewed
deep-supported profile. Task stays `in_progress`.

## Scope

Static Flask routes become Endpoint method and path, with `handled_by`.
`depends_on` is in scope where the suite asserts it. `calls` are in scope.
Negatives: dynamic route, unregistered callable, local flask module, and
ambiguous app selection. Out of scope: new extractors; other stacks;
deep-supported promotion; live eval; AC-RKG-003; AC-RKG-007; AC-RKG-035.

## Acceptance criteria under test

AC-RKG-004, AC-RKG-005, AC-RKG-006, AC-RKG-048.
Verify path: `tests/conformance/test_flask_framework.py`. Append evidence
before marking done.

`tests/conformance/test_flask_framework.py` has three tests on temporary
fixtures, with no repo-test oracle and no census json. It asserts Endpoint
method and path, `handled_by`, a `depends_on` edge, `calls`, dynamic-route and
ambiguous-app negatives, an unregistered callable left off the handler set, a
local flask module that yields no endpoint, `DETECTED_ONLY`, and one-versus-many
app selection. `validate_fact_batch` runs. It does not assert import edges or
a syntax-error sibling. AC-RKG-007 is not under test because
`validate_fact_batch` does not assert evidence locations or rule ids.

## Result

Verify lát recorded: `TEST-RKG-FLASK-001` (`test_flask_framework.py` 3 passed,
on commit `2d0af72…`) and `DIARY-TASK-RKG-047`. The AC-RKG-004 wording
correction is `TEST-RKG-FLASK-001-r2`, and `TEST-RKG-FLASK-001` remains the
verify record. Status remains `in_progress` — deep-support review not closed.
