---
key: PLAN-TASK-RKG-030-r4
group: evidence
system: SYS-RKG
revision: 1
captured_at: '2026-10-06T17:29:32+07:00'
classification: internal
ai_assisted: true
type: implementation-plan
task_key: TASK-RKG-030
previous_plan: PLAN-TASK-RKG-030-r3
context: CTX-TASK-RKG-030-r3
authorization: CR-RKG-012
source_review: REV-RKG-2026-010
---
# PLAN-TASK-RKG-030-r4 — Hoàn thiện physical multiplicity preflight

Standing resume covers only finding001. Findings002/003 are independently resolved in REV010 and their code remains unchanged. Two adversarial rounds have completed; this repair does not authorize automatic round3/merge.

1. RED — tests/integration/test_chatbot_storage.py: invalid MANY_ONE/ONE_MANY/ONE_ONE across all canonical REL tables at version2/3 and CALLS at legacy0/1, with full schema/data/version/applied_at unchanged. Positive canonical caller/callee fan-out/fan-in across supported versions. Add schema-only/no-row-export/cleanup and safe-export-error checks.
2. GREEN — src/rkg/storage/migrate.py: derive expected multiplicity from canonical DDL, default MANY_MANY on pinned Kuzu0.11.3. Read actual multiplicities using EXPORT DATABASE with schema_only=true into a protected ephemeral directory; never fall back to data export, never log schema/path/rows. Validate complete REL mapping before any upgrade or version3 no-op. Keep current default/PK/connection/singleton guards.
3. Run focused storage and full synthetic backend suites, excluding live-provider/pilot; Ruff/diff and 36 normative-pin integrity. No spec, resolved-finding code, operator DB or source execution changes.
4. Append current-tree evidence/diary/remediation record; preserve same001 ID, attribution/fingerprint and resolved002/003. Freeze package r3 for gate authority. No self-review closure or automatic third review; Component Merge remains pending until human workflow decision under B.18.
