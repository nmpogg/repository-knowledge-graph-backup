---
{
  "key": "LCV-RKG-CHATBOT-001",
  "type": "contract-view",
  "group": "derived",
  "revision": 1,
  "non_normative": true,
  "hand_written": false,
  "derived_from": [
    "BL-CHG-RKG-2026-002-r7"
  ],
  "generator": "tools/render_chatbot_l3_view.py",
  "generator_sha256": "d97d244b92de795b1bb88a40c499cfe750bb67ffca1a7e9c52868558d9056d50",
  "source_hashes": {
    "FR-RKG-005": "6f240da74dd108933c85da36bf973106c30b7a6825f2e3b57e67318fa22a78f5",
    "ADR-2026-007": "1f2cacebd38a882af11857e025a17e30b88cab9c91e61637deba623bdf75221a",
    "CMP-RKG-CONVERSATION": "2b2bc1bb8c3cc17cc2349d5c3be07b828efd89cbc24660cfba2c44635adffa65",
    "CMP-RKG-WEB": "9127465096842ccdf6addff5649a13839515f088a136d2bdcbbb3e5ccb5b91e6",
    "TM-RKG": "c22e337412e5c9d42bccbc5cf5ef76e92767ee130f3b4d8a9de86ea6d6570bb6",
    "UXF-RKG-002": "5e57d4c6d118e1463a96373740105d61371514de12f2f1aa17a303206d8e3add",
    "SCR-RKG-001": "385e3bd7ddb7ff32397580270005574cb6cce2ae47e392e7b137c9a4520876c3",
    "UID-RKG-001": "b5b92b6652c087cadaa0a347de226f9bf72fc2f5ad36eff617e9452b4e3dbc7e",
    "GATE-RKG-SCOPE": "bf7f2fb25f44a09f6ce42a3f937a5e125abe4cf184789b0eb9e9e5f304a2ed17",
    "GATE-RKG-ARCHITECTURE": "4730cff2a9093f0ef76b82a67a3eddb5a55090b9a88cef9cf257893b1b0187d6",
    "GATE-RKG-UIUX": "1a2f9c73ad48d1d450e6d537e3af6596971ff356303c50a96d470679a2215787",
    "PRD-RKG": "6406762c3f72ed86601b16711a105408be90b72389891e66dd4642b4ecbc25cc",
    "DOM-RKG-CORE": "24759954cd15951c3c6fc441d0ba0b88d831f62f86ee1e5b1c15db74318d2ff3",
    "CAP-RKG-003": "a83f81a79c97a82bb302f0db2a28ade53e32299b390d45a2318ae33839c57c93",
    "CMP-RKG-GRAPH": "7792b51117fd0d302a1e1d485e06f68f01266a151fe3bf94220ddddb17c6cbb2",
    "CMP-RKG-TRANSPORT": "6d89ca2098b2335b8455b3dad6c2b0a214079e55cd92e13d5cbf0de13e6df286",
    "ADR-2026-001": "ee392713079ebeb4904445a033ce7b5bdfd417a85cfc20e4bac8bde23442c10d",
    "ADR-2026-004": "43ade7152dac2960329b8dd0a196649e91a317c125133a53e7e26164d5f4e3e3",
    "NFR-RKG-SEC-001": "ea54ad8b488bc6bcc862ed0316dc8e6a46a58ad63119b9cadf3d24853d8135aa",
    "NFR-RKG-REL-001": "fd6742188c96da8e9859bbd15ff68715c792e57d6eaf6368d34e3d34dd902b0b",
    "NFR-RKG-UX-001": "c73044ee84ad7fda785daf4ad9818e128d5cf33e02005b00f8019668f09be4e3",
    "API-RKG-CORE-v1": "d73b75134b57955ae827baca16408e91b467ded0b027ccea28f58c7e536b77ce",
    "TBL-RKG-GRAPH": "a624df781b47be8e631dc3e85a1140a555fb5a121012ab6ba929f4c438c305ac",
    "UIS-RKG-001": "d849542a45c36420e35c7aa48d649884832c334224b7b73cc923de9c34e4851d",
    "EVAL-RKG-QA-001": "19bba2089b095b0b431d85d843a61a3d5a4488889c269d47439869f11b673720",
    "OBS-RKG-005": "82acb6483ca288e1952b5f7f354158243ea07ea45cf090a62392787e3c92ef3f",
    "TOK-RKG-001": "ae71b14d8921b6e64f03641a5787c7b99622fa3f28904a75208eabfb32c8de96",
    "DDL-RKG-GRAPH": "b912230b0b7039906ae6fd8b9500a69bdcccff06bbc485ed2f494afadc084de4",
    "MIG-RKG-CHATBOT-v3": "04030c6d33a1780ab8ba5c8247d247b539d28305f9b685aa85485f706798e571",
    "CON-RKG-CONVERSATION-v1": "e66334ee24d46d476acd0920ec9344b0fc34bc84a8bdd8ff054cbaafee9620c4",
    "SCH-RKG-CONVERSATION-v1": "d7991763c99ac815caa5b271045f10d6d0b6743f1b52b82765ddccdbad6cf574",
    "OAS-RKG-CONVERSATION-v1": "fbf37df09fa390bb5155608424bc0c7ce01b7e88940f2fc3d3a4beac32397a02",
    "SCH-RKG-READ-PLAN-v2": "0908b8a657b6b96a1f848ee4cfd511238ed195b871fb8785e6f4d5c33c5d7336",
    "SCH-RKG-NARRATIVE-v1": "8155b0bdc464a4adae07a48911d684bdf01b3afe7b0cb4a5e1624dc3d5f71394",
    "CHL-RKG-CONVERSATION-v1": "3a4539506d1395209c29a1c3adf90a34bf9651c5c338e85080835d5d0010beba",
    "GATE-RKG-CONTRACT": "ec4f6f6b49f1043ca769bfad7d5b96296b04226ac96048d91a3b7f3b1849c919"
  }
}
---

# LCV-RKG-CHATBOT-001 — Chatbot L3 contract candidate

> Normative API/CON/schema/DDL/UIS artifacts win over this view.
> Contract Gate is pending; this is not approval or implementation evidence.

## Exact contract sources

| Key | Revision | SHA-256 | Source |
|---|---:|---|---|
| API-RKG-CORE-v1 | 16 | `d73b75134b57955ae827baca16408e91b467ded0b027ccea28f58c7e536b77ce` | `.aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md` |
| TBL-RKG-GRAPH | 13 | `a624df781b47be8e631dc3e85a1140a555fb5a121012ab6ba929f4c438c305ac` | `.aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md` |
| UIS-RKG-001 | 13 | `d849542a45c36420e35c7aa48d649884832c334224b7b73cc923de9c34e4851d` | `.aide/design/ui/UIS-RKG-001.md` |
| DDL-RKG-GRAPH | 13 | `b912230b0b7039906ae6fd8b9500a69bdcccff06bbc485ed2f494afadc084de4` | `.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher` |
| MIG-RKG-CHATBOT-v3 | 1 | `04030c6d33a1780ab8ba5c8247d247b539d28305f9b685aa85485f706798e571` | `.aide/tech-specs/RKG-GRAPH/schema/MIG-RKG-CHATBOT-v3.cypher` |
| CON-RKG-CONVERSATION-v1 | 1 | `e66334ee24d46d476acd0920ec9344b0fc34bc84a8bdd8ff054cbaafee9620c4` | `.aide/tech-specs/RKG-CONVERSATION/CON-RKG-CONVERSATION-v1.md` |
| SCH-RKG-CONVERSATION-v1 | 1 | `d7991763c99ac815caa5b271045f10d6d0b6743f1b52b82765ddccdbad6cf574` | `.aide/tech-specs/RKG-TRANSPORT/api/SCH-RKG-CONVERSATION-v1.json` |
| OAS-RKG-CONVERSATION-v1 | 1 | `fbf37df09fa390bb5155608424bc0c7ce01b7e88940f2fc3d3a4beac32397a02` | `.aide/tech-specs/RKG-TRANSPORT/api/OAS-RKG-CONVERSATION-v1.json` |
| SCH-RKG-READ-PLAN-v2 | 1 | `0908b8a657b6b96a1f848ee4cfd511238ed195b871fb8785e6f4d5c33c5d7336` | `.aide/tech-specs/RKG-CONVERSATION/llm/SCH-RKG-READ-PLAN-v2.json` |
| SCH-RKG-NARRATIVE-v1 | 1 | `8155b0bdc464a4adae07a48911d684bdf01b3afe7b0cb4a5e1624dc3d5f71394` | `.aide/tech-specs/RKG-CONVERSATION/llm/SCH-RKG-NARRATIVE-v1.json` |
| CHL-RKG-CONVERSATION-v1 | 1 | `3a4539506d1395209c29a1c3adf90a34bf9651c5c338e85080835d5d0010beba` | `.aide/tech-specs/RKG-TRANSPORT/api/CHL-RKG-CONVERSATION-v1.yaml` |
| GATE-RKG-CONTRACT | 9 | `ec4f6f6b49f1043ca769bfad7d5b96296b04226ac96048d91a3b7f3b1849c919` | `.aide/policies/gates/GATE-RKG-CONTRACT.md` |

## Source excerpt: API-RKG-CORE-v1

Revision 16 is the target contract for FR-RKG-005 AC-RKG-074…081, derived from
approved ADR-2026-007 r2/CMP-RKG-CONVERSATION r7. Runtime still implements the
pre-delta contract. Contract Gate is pending; these definitions do not advertise
features in the running server or approve implementation/release.

Machine sources beside this file: `SCH-RKG-CONVERSATION-v1.json` defines public
payloads; `OAS-RKG-CONVERSATION-v1.json` is the conversation-only OpenAPI slice.
Other routes stay governed by their existing sections. Internal model schemas
are owned by Conversation, not exposed in public responses:
`RKG-CONVERSATION/llm/SCH-RKG-READ-PLAN-v2.json` and
`SCH-RKG-NARRATIVE-v1.json`. Application-level conditions below are mandatory
in addition to JSON Schema validation; valid JSON alone is not grounding proof.

### Public extension and negotiation

Existing `/api/v1` paths, status meanings, error envelope, successful POST HTTP
200, and `schema_version=rkg.conversation/1` remain. Old fields are retained.

| Operation | Target addition |
|---|---|
| `GET /conversations/capabilities` | `rkg.conversation-capabilities/1`, nonsecret `provider_enabled` flag + features `ui_locale`, `response_metadata_v1`, `exact_citation_lookup`, `history_unavailable` |
| `POST /conversations/{conversation_id}/turns` | Optional `ui_locale: vi\|en\|null`; null/omitted normalizes to vi |
| `GET /conversations/{conversation_id}/turns` | Optional `include_unavailable=false`; true returns stored history even if pinned graph is unavailable, with `snapshot_available=false` |
| POST result and each GET history turn | Optional nullable `response_metadata`; new terminal turns emit version 1, legacy/pending turns may have null/absent metadata |
| `GET /conversations/{conversation_id}/turns/{turn_id}/citations/{citation_index}` | Exact persisted citation lookup, zero-based index, `rkg.citation/1` |

Capabilities are registered/enabled only when all advertised features are
implemented together. `provider_enabled` is local configured/enabled readiness,
not remote credential health; it exposes no provider config value or credential.
UI disables submit and offers Explorer when false; server independently enforces
the same guard with 503 for direct/old clients. Old server 404 means legacy mode; do not send `ui_locale`
to its extra-forbid POST body, or use new lookup/query behavior. Transient
capability-read errors do not imply legacy or silently enable features. New UI
falls back to locale-absent old requests in confirmed legacy mode and visibly
marks unknown coverage/exact source lookup unavailable. Backend-first upgrade
keeps old clients working; no new field becomes required for old input/history.
Mock/live implement the same negotiated public shape; preview sidecars are not it.

History status includes pending, answered, needs_clarification, insufficient_evidence,
failed and interrupted (restart recovery already exists in the pre-delta runtime).
Fresh successful POST results use the three terminal success statuses; same-key
replay may return the existing pending/interrupted record with HTTP 200, preserving
legacy behavior without a new provider call. Failed provider turns still return
the existing error envelope. The UI treats interrupted as an error/retry state,
not insufficient evidence or an answer.

Default history behavior retains 410 for unavailable graph. The opt-in query is
additive, rather than changing old error behavior to 200. With opt-in, repository
and conversation identity must exist; missing/mismatched identity remains generic
404. Stored transcript/pin never retarget to active snapshot. Unavailable graph
disables selection/submit/source lookup; candidates are empty in the returned
history but persisted pending state is not erased.

### Language, identity and replay

Question is nonblank after trimming, at most 2000 characters on the wire. Locale
must be vi/en/null; unknown locale/unknown input field returns 422 before writes
or provider calls. Identifier and method/path tokens do not count as language
signals. Clear Vietnamese (including unaccented) wins vi; clear English wins en;
otherwise use normalized UI locale. Ordinal/button selection inherits the pending
question's language/locale. The input field is a fallback locale, not an explicit
override of a clearly identified question language.

Fingerprint is SHA-256 of canonical JSON of the exact submitted `question` and
`root_id`, retaining current whitespace/null/empty-string distinctions and the
default-vi legacy payload exactly. Trimming is for lookup/language, not identity. Add
`ui_locale: en` only for nondefault en input. Absent/null/explicit vi therefore
hash identically; en differs and same request key conflicts if changed. Existing
legacy turn hashes/answers are never rewritten. Replay of an existing default-vi
key returns the stored legacy result (metadata may be absent), even if a fresh
turn today would choose another wording. Client retries retain the original body,
root and locale; expected revision is the admission guard, not fingerprint input.
Replayed turn content/metadata/citations are immutable; envelope revision and
candidate state reflect the current conversation, as in the existing contract.

Greeting-only follows session/snapshot/provider-enabled guards, commits a normal
idempotent turn, emits `kind=greeting`, no claims/citations and zero graph/model
calls. It preserves focus and pending intent. Greeting mixed with a graph question
uses normal retrieval. Provider disabled/error/timeout remains 503/502/504, never
an insufficient result. Invalid request/revision writes nothing; accepted turns
still reserve one pending slot and finalize outside provider/network work.

### Persisted response metadata

Version 1 object has exactly: `version`, `language`, `kind`, nullable `subject`,
`coverage`, nullable `retrieval_truncated`, nullable `history_truncated`,
`limitations`, nullable `insufficient_reason`. Subject is server-resolved identity:
entity ID/type/name/qualified name and nullable endpoint method/path. IDs and code
names are not translated; endpoint method/path come from attributes, not a label
guess. The response includes no internal plan, raw source, config value or reasoning.

- `kind`: answer, clarification, greeting, insufficient, error.
- For answer/insufficient kinds, `coverage=partial` when retrieval or history was
  truncated; complete only means no observed truncation within the evaluated
  bounded lookup/context, never all runtime relations. If no factual lookup could
  be evaluated, use unknown. Guidance before factual retrieval remains not_applicable.
- Legacy absent/null metadata is unknown; pending/error work with unobserved
  retrieval may use unknown/null flags. Greeting/clarification before retrieval
  use not_applicable for factual coverage; observed history limits still show.
- Known retrieval/history flags and reason codes are stored, not coordinator-local
  counters. POST mirrors these flags in existing top-level fields; historical
  legacy replay keeps required top-level booleans false for compatibility, while
  metadata absence makes coverage unknown. Consumers must not infer completeness
  from those legacy booleans. GET reads exactly the terminal stored metadata.
- Insufficient reasons: entity_not_found (no root match), relation_not_found (no
  supported requested relation in retrieved context), intent_unresolved (cannot
  resolve what to query), answer_not_supported (facts exist but selection cannot
  support the question). Other kinds use null. A no-match result is not proof of
  absence in source/runtime; a partial result must say its bounded coverage.
- Limits: unique max_chars/max_nodes/max_edges/max_depth/history_truncated,
  containing exactly the observed limits. UI translates these codes to helpful
  language and keeps them beside the answer after reload.

Consistency rules: kind must match status (answered → answer/greeting,
needs_clarification → clarification, insufficient_evidence → insufficient,
failed/interrupted → error). Factual answer has nonnull resolved subject and
known boolean flags. Complete requires both flags false and no limitation;
partial requires at least one true flag and its corresponding observed limit.
Greeting has no factual subject/claims/citations. Only insufficient kind has a
nonnull insufficient_reason. Unknown/unobserved flags are null, never guesses.

### Structured lookup and narrative validation

Read-plan v2 has mode/search query/candidate index/entity type/direction/relation
types. It allows no shell/network/raw query/tool instruction. Mode-specific
irrelevant fields use empty query, candidate_index=0, entity_type=any and empty
relation_types. Candidate indices are zero-based within the committed list.
Any nonempty query/type/direction/relation must be in the allowed schema and
caller intent; model planning does not override explicit IDs or exact method/path.

Local resolution order: valid explicit root/committed selection; explicit new
subject replaces pending intent; otherwise ordinal resumes pending intent;
follow-up focus; conservative exact method/path/type/name lookup; at most one
planner lookup when still unclear. Invalid ordinal retains the same list and
intent without synthesizing from the number. A selected explicit root that belongs
to the pending list resumes that original intent; it is not a new question "2".
Legacy candidate lists without pending intent ask the user to restate the question
and retain the choices until a new intent is supplied; never infer a numeric intent.

Endpoint intent filters Endpoint first. HTTP methods normalize to uppercase;
paths match case-sensitively exactly after surrounding whitespace trim, without
decoding/query stripping/trailing-slash guessing. A full method/path must be an
exact attribute match; path-only/multiple-name matches require explicit choice.
Candidate order is stable type/qualified_name/ID, maximum 20. An overflowed lookup
must clarify/refine rather than choose the first visible page.

Narrative v1 has only `status`, `root_id`, sections of `relation`, `direction` and
paths of `anchor_id` plus ordered edge IDs. Max four sections, eight paths per
section, four semantic edges per path; maximum eight distinct factual edges across
all sections (existing selector bound), excluding endpoint connector introductions.
Schema status insufficient requires no sections; answered requires nonempty
sections. Root equals the resolved subject; types/directions must match the
resolved intent. Incoming/outgoing cannot be mixed to imply caller is callee.

For a Callable root, path anchor is that root. For Endpoint calls/downstream
callable relations, anchor must be a Callable reached by a verified outgoing
handled_by connector in this context. Endpoint-owned handled_by/depends_on queries
may instead anchor at the Endpoint itself; handled_by remains a handled_by claim.
The connector is rendered as endpoint/handler introduction, not calls. Each edge
exists in the same pinned context and has usable evidence; path walks continuously
from the anchor in the section direction, contains no repeated node/edge, and
has the section relation at the last edge for outgoing or first edge for
incoming traversal. All other edges are calls; outgoing calls-prefix paths or
incoming caller continuations may reach reads/writes/events as indirect relations; arbitrary imports/contains fan-out cannot do so. Direct
means one semantic edge from anchor; indirect means multiple verified edges.
Connectors count toward traversal depth/node/edge/character budgets. Retrieval
uses one bounded build_context with connector plus intended relation policy,
depth 4/nodes 50/edges 100/chars 20000, still within 2 model/3 graph calls/30 sec.

Schema/reference/root/direction/topology/evidence violations fail closed with
502 llm_malformed_response; do not salvage valid fragments or add repair calls.
Backend deterministic renderer writes the natural answer from validated facts,
direct before indirect, with collision-safe names. Option A can render independently
validated facts when layout selection is unnecessary; it never repairs malformed
model output. Narrative free-text answer/reasoning fields are rejected.

### Claims, exact sources and recovery

Existing claim text/edge_id and citation snapshot/entity/evidence IDs remain.
New factual claims additionally carry `citation_indexes` pointing into this turn's
citations; new factual citations have `edge_id`, nonempty evidence_id and snapshot
ID. Every claim binds at least one same-edge context evidence. Index bounds,
ownership, evidence membership and pin are checked before terminal persistence.
Connector introduction is also validated/cited but never a calls claim. No claims
or citations for greeting, clarification or insufficient. Never expose a source
excerpt or use legacy `quote` in the UI.

Exact lookup verifies conversation, then turn belongs to it, then citation index,
then pinned snapshot and persisted evidence ID. `entity_id` is contextual only:
an edge's evidence need not belong to its target entity. Fetch that exact evidence
from the pinned snapshot, not all entity detail evidence. Return ID, relative
file_path, provenance, start/end line and rule. Source locations need positive
ordered lines; filesystem locations use null lines, not fake 1/1 syntax markers.
Reject unsafe/absolute/traversing file paths and do not expose excerpts.
Missing legacy evidence ID, out-of-range index or missing same-snapshot evidence
returns generic 404; unreadable pinned graph returns 410; malformed index returns
422. Ownership mismatch remains generic 404. Never repin or substitute evidence.

Response/state/metadata/citations finalize atomically with revision guard. Provider
failure/restart interruption preserves committed focus and pending intent; error
metadata may record only observed flags. The internal intent is server-only and
must not be logged/exported as review evidence. Persistence/migration details are
defined in TBL-RKG-GRAPH r13; UIS r13 binds these exact public fields.

## Source excerpt: TBL-RKG-GRAPH

Revision 13 is a candidate contract, not implemented application behavior. It
retains all 12 node/13 relationship tables, all graph identity/evidence and
snapshot invariants. One nullable `Turn.response_metadata_json STRING` column
implements API-RKG-CORE-v1 r16 ResponseMetadata v1; `usage_json` stays numeric
usage only. No graph node/edge/evidence format or analyzer migration is introduced.

### Physical and logical versions

Target physical SchemaMeta.version is 3, independent of JSON metadata `version=1`,
conversation-state `state_version=2` and public `rkg.conversation/1`.
Existing publisher stamps the physical CURRENT_SCHEMA_VERSION on new snapshot
metadata: after implementation it stamps 3 on newly published snapshots only.
Historical snapshot schema_version values remain immutable/readable; the graph
entity/edge/evidence profile is unchanged by this operational-column migration. Fresh target
bootstrap executes the fenced DDL then inserts exactly one SchemaMeta current/3
row. Candidate MIG-RKG-CHATBOT-v3 executes an atomic 2→3 ALTER plus version update
on Kuzu 0.11.3. The application migration dispatcher remains version 2 until the
implementation task wires this target; current runtime/schema acceptance is not
claimed by executing a fixture migration.

Runner preconditions: exactly one current/2 row and no metadata column. Current/3
with the correct nullable STRING column is a verified no-op replay, leaving the
original applied_at unchanged. Other versions or partial/unexpected shapes refuse
without writes; version 0/1 must use existing migrations to reach 2 first. A failed
ALTER/metadata update rolls back the transaction. If Kuzu has already aborted it,
the runner must tolerate rollback of an aborted transaction without hiding the
original failure. Never drop user tables/database to upgrade.

New column is null for every old row; migration never rewrites transcripts,
claims/citations, focus, candidate order, request hashes, turn IDs, revisions,
timestamps, graph facts or snapshot pins. New writes validate metadata against
SCH-RKG-CONVERSATION-v1 ResponseMetadata and application consistency rules before
committing it with the terminal turn. Never store provider prose/reasoning/context
or source/config values in metadata. Maximum metadata JSON size: 8192 UTF-8 bytes;
IDs/relative paths/subject labels must pass existing data minimization. Unknown
future metadata versions map to unknown coverage; the reader must not manufacture
false truncation flags or a success badge.

### Conversation.state_json v2

Retain `focus_entity_id` and `pending_candidate_ids` for existing readers. Add
`state_version=2` and nullable `pending_intent`, with exactly:

| Field | Constraint |
|---|---|
| question | Original redacted, trimmed business question, ≤2000 characters; never the ordinal reply |
| ui_locale / language | Normalized original fallback locale and effective answer language, vi/en |
| relation_types | Unique allowed graph relation names, stable order |
| direction | incoming or outgoing from resolved intent |
| entity_type | Canonical query type or any |
| candidate_ids | Ordered unique domain IDs, ≤20, exactly equal to pending_candidate_ids |

The enclosing conversation pin supplies repository/snapshot ownership; no mutable
pin is duplicated in this JSON. Entire state_json remains redacted and ≤32768
UTF-8 bytes. Old state lacking state_version/pending_intent remains readable;
migration does not infer its original question. Legacy pending IDs without intent
must ask for a restated question, not synthesize from a number. No source raw text,
language-model tool instruction or transcript export is part of state.

### Commit/replay/recovery

Admission uses the existing request key and revision, stores a pending Turn and
advances conversation revision once. Locale/fingerprint rules follow
API r16; default vi retains the legacy fingerprint payload. Provider/network
calls run outside the transaction. In one guarded terminal transaction write
answer/resolved_question, validated claims/citations, usage, response metadata,
focus and pending state. Clarification writes the original intent and candidate
IDs atomically; a valid choice clears that intent after success. Greeting and
invalid ordinal preserve it. An explicit new subject replaces it only through a
successful committed result, never on provider failure.

Idempotent replay reads stored metadata and rendered answer; it does not recreate
them from coordinator-local flags or rerun language/model selection. Error/restart
preserves committed focus/pending intent, marks the pending turn failed/interrupted,
and records only actually observed metadata (or null if unavailable). No state
cleanup secretly discards another turn's pending intent. Provider errors and
insufficient results remain distinct. Logs/evidence contain IDs/codes/revisions,
not question/answer/state JSON or credentials.

### Rollout and rollback

Stop writer/single-worker service before applying a tested migration, make a local
protected backup, migrate without transcript backfill, then start metadata-aware
backend before a feature-negotiating frontend. No migration is applied to the
operator's database as part of contract drafting. Consumers need acknowledgement
at Contract Gate; backend and web deployment remain implementation work.

Version-2 application refuses a version-3 database. Rollback therefore restores
the protected pre-upgrade backup with the older binary; it is not an in-place
version downgrade or dropping the metadata column. New turns since upgrade would
not exist in that backup: stop writes and require operator decision before rollback.
Backup paths/contents are never included in generated evidence. Downgrade/restore
is not performed by this contract-preparation task.

## Source excerpt: UIS-RKG-001

Revision 13 is the level-4 candidate derived from approved UXF-RKG-002 r5,
SCR-RKG-001 r9 and UID-RKG-001 r8, governed by API r16/TBL r13. Contract Gate is
pending; neither production client nor backend implements these additions yet.
The source design hashes signed by approval-010 are unchanged. This binding
does not introduce another chat page, status enum or visual system.

| AC | Binding / assertion |
|---|---|
| AC-RKG-074 | Negotiated optional ui_locale, persisted metadata.language; UI copy stays in interface locale while answer uses effective language |
| AC-RKG-075 | Candidate type/qualified name and Endpoint attributes.method/path; no client-side guessing of backend subject |
| AC-RKG-076 | Render backend answer once; direct/indirect and connector semantics validated server-side; client never composes facts from IDs |
| AC-RKG-077 | Stable candidate array order; explicit button submits matching root ID and ordinal with current revision/new key; original intent/locale resumed server-side |
| AC-RKG-078 | kind=greeting, safe guidance without facts/sources; provider/session/snapshot guards still apply |
| AC-RKG-079 | Backend reason-specific answer, no second insufficient paragraph; provider/disabled/timeout separate banners, draft retained |
| AC-RKG-080 | Each GET turn.response_metadata supplies limitation/coverage; missing/null/unknown version shows unknown; collapsed claims and one answer |
| AC-RKG-081 | Turn-specific zero-based citation route verifies exact evidence ID and pin; safe relative location/provenance, loading/unavailable and keyboard dialog |

Turn arrays remain paged sequence-ascending; preserve previous pages when loading
more and deduplicate by turn ID, not text. Read metadata from each stored turn,
not a flags map populated only by submit. History's current candidate list/revision
is the selection state; old clarification turns do not create live selectable
buttons. Greeting history does not clear an active pending clarification.
Capability/cache and history requests must be tied to the current backend origin
and pinned conversation; never reuse one conversation's metadata for another.

Source buttons always have a nonempty visible/accessibility label (e.g. Source 1).
Exact path/line may be shown only after the dedicated lookup returns the matched
evidence. Do not guess location from entity_id, quote or entity detail. Use
encodeURIComponent for all IDs; citation index is the ordinal within the stored
citations array, unaffected by dialog opening order. Before showing the location,
check returned conversation/turn/pin/index and evidence ID equal the requested
stored citation. A mismatch becomes unavailable, not another source.

Unknown coverage is a distinct notice, not complete/no-truncation. Even complete
within-budget metadata does not license copy such as "all functions". New-client
legacy-server mode may display old safe answers and readable source ordinals, but
must explain exact source lookup/coverage is unavailable; it cannot pretend its
old adapter has provided the new contract. Mock fixtures use identical public
schema and version/capability transitions, replacing preview-only sidecars.

New error rendering must wait for/reconcile any required history reload before
setting the banner, so reload does not clear it. Stale revision preserves the
draft and offers reload/review/retry; it does not auto-resubmit. Keyboard, focus,
safe text, touch/long-name wrapping and reduced motion inherit approved UID.
No question/answer, tokens, credentials or raw source is added to telemetry.
