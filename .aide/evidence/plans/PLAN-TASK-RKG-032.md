---
key: PLAN-TASK-RKG-032
group: evidence
system: SYS-RKG
revision: 1
type: implementation-plan
task: TASK-RKG-032
change_set: CHG-RKG-2026-002
---
# PLAN-TASK-RKG-032 — Validated narrative and natural answer

1. RED: tests/unit/test_conversation_narrative.py exercises pinned root/anchors, cycles, foreign edges, reversed incoming, missing evidence, schema extras, status consistency and eight-edge aggregate cap.
2. GREEN: conversations/narrative.py loads approved narrative schema; validate complete selections against the bounded ContextPackage, verified Endpoint→handler connectors and requested relation/direction. Render collision-safe vi/en direct and indirect paths; exact claims/citation indexes cite each used edge.
3. GREEN after TASK031 review freeze ends: grounded.py loads read-plan v2/narrative v1, validates profile/sentinels and deterministic intent precedence, uses one context build for connector plus calls/semantic edges, normalizes depth-limit metadata and preflights full schema/messages within8000 tokens by trimming oldest history. No repair or salvage.
4. service.py retains citation edge_id and validates exact claims/citation bindings before terminal persistence. Update existing synthetic test provider fixtures for the new schema; legacy output remains rejected by runtime.
5. Verify targeted narrative/grounded/provider/persistence regressions, Ruff, budget counters and current hashes. Freeze code/tests/contracts for independent adversarial review, max two rounds; preserve reviewer IDs.

No signed specification edits, analyzed source execution, operator migration or live-provider acceptance. TASK033 owns public metadata/history/capabilities/exact-source routes.
