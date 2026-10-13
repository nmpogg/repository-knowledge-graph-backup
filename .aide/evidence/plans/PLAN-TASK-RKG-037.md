---
key: PLAN-TASK-RKG-037
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-037
---
# PLAN-TASK-RKG-037 — Add direct OpenAI provider

1. Specify explicit RKG_LLM_PROVIDER selection, default openrouter; selected missing key is disabled, invalid selector fails safely, no cross-provider fallback. Preserve budgets and public API shape.
2. Add failing adapter/config tests for OpenAI-only payload, fixed official endpoint, correct key/model, strict schema projection, original local validation, safe transport/refusal/shape errors and optional finite budgets.
3. Implement stdlib transport and shared completion validation. Only wire schema drops artifact annotations and unsupported uniqueItems; string enums acquire their equivalent type. Original schemas and graph validation remain authoritative.
4. Load new server env keys; document both providers and correct stale root README budget text. Revise current component/contract, retain historical approvals and pending gates.
5. Verify backend regression and provider selection through API. Freeze current normative/source hashes; independent reviewer checks candidate (maximum two full rounds). No paid live calls; provider model support remains an external prerequisite. Mark implementation done only with current-tree evidence; gates remain pending.
