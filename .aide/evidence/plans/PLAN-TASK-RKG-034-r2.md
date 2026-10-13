---
key: PLAN-TASK-RKG-034-r2
group: evidence
revision: 2
type: implementation-plan
task: TASK-RKG-034
supersedes: PLAN-TASK-RKG-034
---
# PLAN-TASK-RKG-034-r2 — Review repairs

1. Preserve REV-TASK-RKG-034-001 and its independent probes. Add regression coverage for valid relative source paths, control characters, unknown v1 coverage and late submit after route change.
2. Correct path escaping; explicitly display unknown coverage. Guard submit success, failure and finally with route/request generation; reset pending/draft state on conversation change so stale responses cannot refresh or alter the next conversation.
3. Run frontend regressions, full suite, build/lint. Freeze r2 with all current candidate hashes and unchanged 36 normative pins; independent reviewer verifies original findings and current contract. No automatic third round.
