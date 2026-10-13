---
key: PLAN-TASK-RKG-036
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-036
---
# PLAN-TASK-RKG-036 — Remove chatbot application ceilings

1. Align current normative revisions with explicit CR-RKG-018; preserve signed baseline/approval history and set affected gates pending. No graph table shape migration; DDL declares updated semantic TBL revision.
2. RED: default budget accepts more than2 model/3 graph operations, over8000 input/1500 output tokens and elapsed30s; default adapter omits completion cap and uses no turn timeout. Keep explicit finite budgets testable and provider timeout/error/schema handling safe.
3. GREEN: nullable defaults mean no application ceiling; retain usage counters, provider/schema validation and privacy safeguards. Remove grounded8000 preflight/history trimming caused by that ceiling. History6/4000 and graph depth4/50nodes/100edges/20000chars,8 distinct semantic relations stay unchanged.
4. RED/GREEN: remove question character cap from service, mock, UI and pending-intent schema/storage; count only bounded state envelope excluding the original question so long ambiguity survives reload/replay. Preserve nonblank/type/idempotency/redaction checks and unrelated path/name limits.
5. Run backend/frontend contract and regression checks/build/lint; execute revised DDL only on temporary fixture, never operator DB/live LLM. Freeze exact candidate evidence for independent review. Gate approvals require a later concrete human decision; earlier approvals are not transferred.
