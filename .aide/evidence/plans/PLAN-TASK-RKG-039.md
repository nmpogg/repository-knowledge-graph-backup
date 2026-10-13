---
key: PLAN-TASK-RKG-039
type: implementation-plan
group: evidence
revision: 1
task: TASK-RKG-039
---
# PLAN-TASK-RKG-039 — Verbose terminal debug mode

1. Honor explicit user opt-in terminal-detail authorization; no broad framework/HTTP credential logging. Configure dedicated application console handler from serve --log-level info|debug, info default. Do not globally enable third-party DEBUG or change app behavior.
2. RED/GREEN actual subprocess console visibility, handler idempotency, configured-key masking, info excludes prompt/response detail, debug emits full model request/response and validation paths. ContextVar correlation resets per turn and isolates concurrent turns.
3. Log stage start/end/elapsed and model/graph counters; retain existing rejection event codes. Add debug HTTP body and local JSON/schema/graph validation details before safe error mapping, no retry or graph guard change.
4. Document restart command; no operator .env/database, process restart or live provider invocation. Raw terminal debugging is explicitly authorized but not copied into evidence/history/API/storage.
5. Run affected backend/API/provider and frontend-startup checks, freeze existing normative hashes and source candidate; independent reviewer max2 rounds. Done is bounded implementation, human/source/component gates pending.
