---
key: DIARY-TASK-RKG-038-r1
type: implementation-diary
group: evidence
revision: 1
task: TASK-RKG-038
---
# DIARY-TASK-RKG-038-r1 — Malformed-turn repairs

Generic stored rejection cannot establish live cause. Operator reports both
providers, pointing investigation at shared stages without proving a defect in a
specific response. No live response/transcript capture or operator config edits.

Existing CON requires allowed anchors/connector references; runtime now sends
those IDs and per-anchor path bounds explicitly. Predicate/connector helpers are
shared with unchanged validator checks. Exact root/edge-ID, direction, path and
planner sentinel instructions remain subject to original strict schema/graph checks.

Static allowlisted WARNING codes distinguish planner, narrative schema and graph
rejection, with no dynamic exception/result/input fields. UI explains malformed
turn naturally, keeps technical code in closed details, omits coverage/limit notes
for failed/interrupted/pending. Legacy completed metadata behavior remains.

Independent round1 FND038001 confirms unexpected custom-provider paths lacked
warning diagnostics. RED two probes; repairs preserve existing provider_failed
mapping/state/one attempt while warning provider_failure or response_shape.
Author104 affected checks pass. Source/component decisions pending; live incident
root cause and human UAT unverified. No product schema/storage revisions.
