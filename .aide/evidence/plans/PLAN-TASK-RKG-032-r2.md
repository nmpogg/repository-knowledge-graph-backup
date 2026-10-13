---
key: PLAN-TASK-RKG-032-r2
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-032
---
# PLAN-TASK-RKG-032-r2 — Repair round1 narrative findings

1. RED: add dispatch tests for all13 explicit relations, collision-renderer tests with same qualified names in distinct files, and indirect write wording assertions.
2. GREEN FND001: grounded.py identifies every supported relation (including unaccented Vietnamese), keeps the explicit relation allowlist, and preserves connector/semantic retrieval when no relation is yet known.
3. GREEN FND002: narrative.py disambiguates rendered identities by qualified name, then safe relative file/line and full stable ID when necessary.
4. GREEN FND003: narrative.py labels every indirect path hop using its verified relation verb; incoming paths retain actual source→target roles.
5. Verify current-tree synthetic backend (exclude prepared TASK033 RED cases), lint and whitespace; freeze r2 and independent re-review with original IDs/fingerprints.
