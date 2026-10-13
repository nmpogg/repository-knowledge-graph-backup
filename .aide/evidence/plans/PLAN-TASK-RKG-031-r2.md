---
key: PLAN-TASK-RKG-031-r2
group: evidence
system: SYS-RKG
revision: 1
type: implementation-plan
task: TASK-RKG-031
---
# PLAN-TASK-RKG-031-r2 — Repair independent round1 findings

1. RED: extend tests/unit/test_conversation_language.py for opposite-locale clear explanatory/listing prose and natural endpoint/Callable names; extend tests/integration/test_conversation_resolution.py for planner candidate selection resuming committed v2 intent and preserving legacy choices.
2. GREEN FND001: grounded.py uses stored intent for all planner candidate selections, with original language/question/relation/direction; invalid or legacy model choices preserve state and request restatement.
3. GREEN FND002: resolver.py prefers entity-kind name before does fallback, preserving explicit Endpoint/Callable type.
4. GREEN FND003: language.py recognizes clear Vietnamese accents/prose after identifier exclusion and English listing/invocation signals.
5. Verify current-tree targeted suite, Ruff/whitespace and frozen normative hashes; submit second adversarial review retaining all three IDs/fingerprints from REV-TASK-RKG-031-001. No changes to signed contracts or historical evidence.
