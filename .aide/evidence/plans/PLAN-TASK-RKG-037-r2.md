---
key: PLAN-TASK-RKG-037-r2
group: evidence
revision: 2
type: implementation-plan
task: TASK-RKG-037
supersedes: PLAN-TASK-RKG-037
---
# PLAN-TASK-RKG-037-r2 — Review repairs

Retain original implementation scope. After REV-TASK-RKG-037-001, reproduce and repair only FND037001/002 plus accepted advisory003:

1. RED/GREEN synthetic HTTPS redirects301/302/303; reject every redirect without forwarding credentials on both fixed endpoints. Retain safe HTTP/timeout/JSON mappings.
2. RED/GREEN invalid selected provider through CLI serve: exit1 and safe JSON llm_invalid_request, no traceback.
3. Conservatively omit string minLength/maxLength on OpenAI wire only; validate the unchanged original schema locally. Retain documented numeric/array wire bounds. Revise draft provider contract/component and invalidate new candidate pins; no approval transfer.
4. Re-run backend and affected frontend startup tests, freeze a new baseline/package/evidence, then request the second/final independent review. Live-provider quality remains not_run.
