---
key: PLAN-TASK-RKG-030-r3
group: evidence
system: SYS-RKG
revision: 1
captured_at: '2026-10-06T17:07:25+07:00'
classification: internal
ai_assisted: true
type: implementation-plan
task_key: TASK-RKG-030
previous_plan: PLAN-TASK-RKG-030-r2
context: CTX-TASK-RKG-030-r2
authorization: CR-RKG-012
base_code_commit: b91d8b7223cc968350fdf5b9ce7feb67506a2dbf
---
# PLAN-TASK-RKG-030-r3 — Sửa ba blocker độc lập

Viết trước regression/production changes trên worktree feat/chatbot-storage-revision từ checkpoint b91d8b7. Giữ signed baseline r8 và REV009 nguyên bytes; không triển khai TASK031–035.

1. RED — tests/integration/test_chatbot_storage.py: malformed old schema (missing/type/table/relationship/PK), singleton rows, refusal with zero mutation on versions0/1/2/3; factual answer coverage unknown/not_applicable, clarification/insufficient facts; greeting clear/replace/focus mutation preserve committed state via failed result. tests/unit/test_chatbot_metadata.py bổ sung metadata semantic negative/positive cases. Chạy trước fix, ghi fail đúng các finding.
2. GREEN — src/rkg/storage/migrate.py: derive physical table/column/type/PK/relationship shape from canonical DDL, account only for supported version0/1/2 deltas; verify whole SchemaMeta singleton, metadata absent/present and complete old shape before any migration write. Keep valid chains/no-op and rollback.
3. GREEN — src/rkg/storage/conversation_json.py: factual answer coverage complete/partial only; no claims/citations in greeting/clarification/insufficient; retain valid unknown insufficient/error and legacy None.
4. GREEN — src/rkg/conversations/service.py: greeting kind owns preserve invariant; reject clear/replace, pending payload or changing focus before terminal writes, even when action omitted. Keep legacy metadata-absent behavior.
5. Affected tests plus full synthetic backend regression (exclude two live-provider modules and pilot), Ruff/diff; new current-tree evidence and diary revision. All work in isolated worktree; no operator DB, live provider, source execution or spec edits.
6. Freeze RVP task r2 and re-review prompt with same finding IDs/attribution/fingerprints. Author marks remediation implemented_pending_independent_verification, never resolved by self-review. Task stays in_progress and Component Merge pending.
