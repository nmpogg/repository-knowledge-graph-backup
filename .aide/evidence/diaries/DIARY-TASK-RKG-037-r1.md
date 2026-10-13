---
key: DIARY-TASK-RKG-037-r1
type: implementation-diary
group: evidence
revision: 1
task: TASK-RKG-037
---
# DIARY-TASK-RKG-037-r1 — Direct OpenAI implementation

## Decisions

- Explicit server selector defaults to existing OpenRouter; both keys can coexist, but only the selected key is used. No client endpoint control, new SDK dependency or cross-provider fallback.
- Shared safe completion lifecycle and bounded transport keep usage, optional finite internal budgets and original local validation. Default application ceilings remain absent.
- OpenAI uses fixed official Chat Completions, strict schema and store=false. Wire projection excludes artifact annotations and local uniqueness; string enums receive their equivalent type.
- Current component/contract candidates document the provider extension; source/component gates stay pending and historical records are immutable.

## Review repairs

REV-TASK-RKG-037-001 confirms redirect credential forwarding and uncaught invalid-selector CLI error. Synthetic regressions fail before repairs; transport now rejects all redirects and CLI handles LLMError through safe JSON/exit1. Accepted advisory string-length uncertainty is addressed conservatively on the wire, retaining original schema validation. Numeric/array bounds remain.

## Verification boundary

Only synthetic HTTP, temporary graph/storage and frontend loopback fixtures. No operator configuration/database, real API key, paid model invocation, deployment or human approval. Live model support/quality stays not_run.
