---
key: CON-RKG-CONVERSATION-v1
type: component-contract
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 4
change_set: CHG-RKG-2026-004
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  owned_by: [CMP-RKG-CONVERSATION]
  satisfies: [FR-RKG-005]
  constrained_by: [ADR-2026-007, NFR-RKG-SEC-001, NFR-RKG-REL-001, API-RKG-CORE-v1, TBL-RKG-GRAPH]
classification: internal
ai_assisted: true
---
# CON-RKG-CONVERSATION-v1 — Internal grounded conversation contract

L3 target for the approved chatbot delta, not current runtime implementation.
JSON schemas under `llm/` are normative model outputs; public fields are defined
by API r16/SCH-RKG-CONVERSATION-v1, and persistence by TBL r13. Contract Gate is
pending. The current service DTOs/planner/selector are pre-delta and must be
replaced in new implementation tasks after readiness, without editing signed L2.

## Service boundary

| Input/output | Target fields and ownership |
|---|---|
| Turn input | Existing question/request key/revision/root plus optional UI locale; validation, exact-body fingerprint and redaction before provider |
| Turn context | Pinned repository/snapshot, redacted question, effective language/fallback locale, committed focus, ordered pending IDs and nullable pending intent |
| Coordinator result | Existing backend-rendered answer/resolved question, validated claim/citation DTOs, focus update, candidate summaries/IDs, usage/context IDs plus typed response metadata and optional pending-intent update |
| Finalized output | Persisted Turn/metadata and committed Conversation state; HTTP never constructs flags from a fresh empty coordinator during replay |

Pending-intent update is explicit preserve/replace/clear. Greeting/invalid ordinal
preserve, new clarification replaces, successful selected/new-topic answer clears
or replaces as appropriate. Provider failure/interruption always preserves the
previous committed state. Candidate summaries are safe graph metadata from one
bounded lookup/batch read, not 20 unbudgeted per-ID graph operations. They use the
same order as persisted pending IDs; stale/unavailable IDs cannot be silently
removed to make a different ordinal select another entity.

Provider local availability is checked without network/model/graph facts lookup:
configured/enabled allows greeting, disabled returns llm_disabled. "Enabled" is
local configuration availability, not proof that a remote credential/provider
will succeed. Session, revision and pinned-catalog guards still apply. Ordinary
Q&A may subsequently fail with the existing provider error/timeout mapping.

## Model boundary

- StructuredProvider.complete receives bounded redacted messages and one of the
  schema-bound read-plan/narrative profiles, never Storage, shell, network tools,
  raw queries, raw source or configuration values. Adapter enables schemas as a
  coherent backend release; it does not accept old edge-list output as narrative.
- Read planner is used at most once when deterministic root/intent lookup cannot
  resolve. Explicit entity/type/method/path and committed selection win over a
  model suggestion. Nonapplicable fields follow API r16's sentinel values.
- Narrative input has redacted resolved question/language, resolved subject,
  allowed anchors/connector references and supported facts: edge ID/type/source
  ID/target ID/evidence IDs, collision-safe labels and truncation metadata. Evidence
  locations are relative and source-free. It also contains the resolved relation
  and direction so a model cannot switch the question to another traversal.
- Narrative output contains only root/section/path references. Backend checks
  structure and graph entailment before rendering the actual answer. The provider
  has no factual free-text answer field, and its internal plan is not returned
  to browser/history/logs. No repair/paraphrase/model-driven source fetch call.
- Bind root/anchor/edge allowlists to the supplied context locally and validate
  all IDs, traversal direction, continuous paths/no cycles, requested relation
  endpoint and usable same-snapshot evidence. JSON Schema validation does not
  prove topology/entailment. Validate the complete selection, not a salvaged subset.

## Budget and retrieval boundary

Application defaults impose no ceiling on model-call count, graph-operation count,
input tokens, output tokens, total provider deadline or user question characters.
A null internal budget value means no ceiling; usage counters remain observable.
The adapter omits max_completion_tokens and passes no total-turn timeout.
Optional explicitly finite internal requests may still enforce their own limits.
Provider/model context, completion limits and transport failures remain external.
History stays at six completed turns/4000 tokens; trim oldest history only for that
window and persist history_truncated/context_turn_ids. Do not trim history or reject
the minimal context because of the retired 8000-token application ceiling. Local context truncation must maintain root/connector
and referential integrity and publish its observed truncation flags.

Endpoint calls use verified handled_by bridge to handler plus intended incoming
or outgoing calls/access path in one bounded graph build operation. Default
depth4/nodes50/edges100/chars20000 apply to bridge plus semantic edges; no per-hop
graph/model tools. Table/event incoming queries use reverse paths to identify
verified upstream participants, rendering the original edge direction accurately.
Path-only/name/type collision and lookup overflow remain clarification, not
automatic first-result choice. Exact method/path is an attribute predicate before
paging; substring search is not proof of uniqueness or exactness.

## Rendering, persistence and failures

Backend renderer uses validated facts and effective vi/en language. Short names
only when unique within the rendered subject/facts; otherwise qualified identities.
Direct relations precede indirect paths, with Endpoint→handler introduction and
incoming caller/callee roles explicit. It cannot infer business semantics from
names or say "all" under bounded coverage. Option A is a deliberate deterministic
layout choice over independently validated facts, never a recovery for malformed
schema/foreign IDs/topology/evidence. Invalid provider output fails closed as
llm_malformed_response; no new facts, no second provider repair.

Claims and citation indexes bind exact same-edge evidence. TBL r14 terminal
transaction stores answer/claims/citations/metadata/state atomically. Metadata
exceeding its byte bound fails closed as llm_budget_exceeded rather than truncating
IDs/flags or committing misleading state. Legacy turns/state remain read-only;
unknown metadata is not treated as complete. No raw transcript is emitted in logs
or generated verification artifacts. API r17 owns exact source lookup and default
locale-preserving idempotency; UIS r13 owns one-answer/disclosure/source flow.

## Contract verification versus implementation acceptance

Author schema/DDL/migration/diff fixtures validate this contract candidate, not
AC implementation, deployment, client integration or live-provider quality.
Independent review and named Tech Lead/QA/consumer acknowledgement remain
Contract Gate work. New tasks must cover malformed/foreign/disconnected/cyclic
paths, reversed callers, insufficient/partial/legacy replay, greeting guards,
clarification restart, exact-source ownership and bounded resource consumption.

CHG-RKG-2026-003 changes validation only: physical SchemaMeta remains version3;
existing MIG-RKG-CHATBOT-v3 r1 still upgrades the identical physical table shape.
The bounded32KiB state envelope excludes pending_intent.question, while metadata
and candidate/state structure constraints remain unchanged.

## Provider selection — CHG-RKG-2026-004

Server-only `RKG_LLM_PROVIDER` selects `openrouter` (default, backward compatible)
or `openai` (direct official Chat Completions endpoint). Each adapter uses only
its own server API key/model settings. Missing selected key is `llm_disabled`,
regardless of the other key; no automatic fallback or client endpoint override.
Invalid selector fails server initialization with safe `llm_invalid_request`;
the CLI returns exit1 and a safe JSON error code without a traceback.
Both fixed-endpoint transports reject every redirect without forwarding credentials.
Provider capabilities expose local selected-key availability only. Injectable
synthetic providers retain the existing testing boundary.

OpenAI uses strict JSON-schema Structured Outputs and `store=false`, without
OpenRouter-only routing/usage extensions. Wire projection removes artifact
annotations (`$schema`, `$id`, `x-aide`), `uniqueItems` and string-length
constraints (`minLength`, `maxLength`); all-string enums gain
their equivalent string type. Original model schemas remain unchanged and must
validate every returned value locally, including uniqueness and string lengths.
String lengths are omitted conservatively because documented base-model wire
support is ambiguous; numeric/array bounds remain on the wire. The coordinator
still validates graph IDs, topology and evidence before rendering. Refusal and
malformed choice/message/content fail closed through the existing safe codes.
No application budget ceiling is restored; existing history/retrieval limits stay.

This revision is an implementation candidate. Source and Component Merge gates
remain pending; previous approvals do not approve this revision. Live provider
quality and credential/model availability require separate operator verification.
