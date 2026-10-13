---
key: PLAN-TASK-RKG-038
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-038
---
# PLAN-TASK-RKG-038 — Malformed-turn diagnostics and guidance

1. Keep observed generic error distinct from unverified live root cause. Reproduce misleading failure/coverage display and missing model input guidance with synthetic fixtures. No operator config, transcript or live response capture.
2. Implement existing CON input contract: explicit allowed anchors/connector references and per-anchor depth bounds; exact root/edge-ID and direction ordering guidance. Add planner sentinel instruction matching existing runtime validator. Never normalize invalid graph references or invent a factual fallback/retry.
3. Distinguish safe allowlisted JSON/schema/content/shape/refusal rejection reasons and planner/narrative/grounding stages in operational logs, never dynamic request fields, raw exceptions or responses. Keep public/persisted error codes and storage shape unchanged.
4. Show natural-language malformed-turn failure (preserve technical code for support), hide coverage/limit notes for failed/interrupted/pending turns; legacy successful responses retain unknown coverage. Add English/Vietnamese regression assertions.
5. Verify backend/frontend, freeze hashes and independent adversarial review (max two full rounds). Done means bounded implementation; exact reported live failure remains unverified without fresh staged diagnostic. Gates remain pending; no normative product contract revisions required.
