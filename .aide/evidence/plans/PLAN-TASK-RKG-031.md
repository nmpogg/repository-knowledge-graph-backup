---
key: PLAN-TASK-RKG-031
group: evidence
system: SYS-RKG
revision: 1
type: implementation-plan
task: TASK-RKG-031
change_set: CHG-RKG-2026-002
---
# PLAN-TASK-RKG-031 — Language, lookup and clarification

1. RED: add tests/unit/test_conversation_language.py and tests/integration/test_conversation_resolution.py for identifier exclusion, exact endpoint attributes before paging, collisions, greeting guards and committed intent resumption.
2. GREEN: add conversations/language.py and resolution.py; extend graph/search.py with exact predicates before pagination and batch candidate lookup. Preserve existing public substring search.
3. GREEN: extend conversations/identity.py and service.py optional validated ui_locale, preserving default legacy fingerprints and carrying locale into TurnContext. Add local provider availability method to llm/openrouter.py.
4. GREEN: update grounded.py to resolve language/subject conservatively, return metadata, preserve greeting/invalid ordinal state and commit original pending question for selection/restart. Keep synthesis contract unchanged until TASK032.
5. Verify meaningful new tests, relevant existing persistence/graph/provider regressions, Ruff and current-tree hashes. Freeze candidate package containing only normative pins, code/tests and test result references (no plan/diary).
6. Independent adversarial review, maximum two rounds; repair only findings. Keep gate pending until authorized decision; never invent live-provider or UAT results.

Current-branch implementation is explicitly authorized by CR-RKG-014. Signed contracts remain byte-identical. Follow-up TASK032 adds narrative topology/rendering, TASK033 wires API, TASK034 updates existing Ask, TASK035 verifies complete AC paths.
