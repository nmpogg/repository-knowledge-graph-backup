---
uid:
key: API-RKG-CORE-v1
type: api-contract
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 17
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  owned_by: [CMP-RKG-TRANSPORT]
  satisfies: [FR-RKG-001, FR-RKG-002, FR-RKG-003, FR-RKG-004, FR-RKG-005]
  constrained_by: [NFR-RKG-PERF-001, NFR-RKG-SEC-001, NFR-RKG-REL-001, TBL-RKG-GRAPH]
classification: internal
ai_assisted: true
---
# API-RKG-CORE-v1 - Core API v1

> Owned by `CMP-RKG-TRANSPORT`. Key `API-RKG-CORE-v1` giữ nguyên để không phá
> traceability FR/UIS/task hiện có; thư mục theo CMP-slug (`RKG-TRANSPORT`).

Base path `/api/v1`. JSON fields/enums trong contract này dùng chung cho backend,
CLI client và frontend. Mutation `/api/*` yêu cầu `X-RKG-Session` cùng loopback
Origin/Host hợp lệ. Snapshot ownership luôn được kiểm tra ở server; client không
thể ghép `repository_id` với snapshot của repository khác.

## Snapshot resolution

Một contract cho mọi graph read:

- `GET /entities`, `GET /entities/{id}` và `GET /subgraph` nhận `snapshot_id`
  hoặc `repository_id`. Có cả hai thì snapshot phải thuộc repository đó. Chỉ có
  `snapshot_id` thì server tìm repository của snapshot. Chỉ có `repository_id`
  thì server dùng `active_snapshot_id`; không có active snapshot trả
  `409 no_active_snapshot`. Thiếu cả hai trả `422 invalid_request`.
- `GET /technologies`, `GET /dependencies` và `GET /diagnostics` bắt buộc
  `snapshot_id`. Không có fallback active snapshot.
- `POST /context` bắt buộc `snapshot_id` trong body. Thiếu body field là
  `422 invalid_request`, không phải `409 no_active_snapshot`.
- `POST /conversations` để trống `snapshot_id` thì pin active snapshot, hoặc
  `409 no_active_snapshot` khi repository chưa có active snapshot. Đó là
  conversation create, không phải graph read.

## Repository contract

Create body có `display_name`, source local và optional defaults:

- local: `source_type=local`, `path`, optional `source_root`;
- optional: `app_module`, `app_symbol`, `scan_defaults`.

`path` luôn được resolve trên cùng host đang chạy RKG và phải nằm trong
`allowed_local_roots`; API không upload source và không diễn giải path trên máy client.

Server canonicalize source identity, từ chối duplicate identity bằng `409
repository_conflict`, lưu locator đã redact cho response. Source identity bất biến
sau create. PATCH nhận `expected_revision` bắt buộc và chỉ cho phép `display_name`,
`source_root`, `app_module`, `app_symbol`, `scan_defaults`.

Repository response gồm `repository_id`, `revision`, `display_name`, `source_type`,
`source_locator_redacted`, mutable defaults, nullable `active_snapshot_id`,
`created_at`, `updated_at`. List dùng `offset`, `limit`, optional `q`; order
`updated_at DESC, repository_id ASC`.

## Endpoints

| Method/path | Input | Success |
|---|---|---|
| `POST /repositories` | repository create body | `201` repository; không tạo job |
| `GET /repositories` | `q`, `offset`, `limit` | paged repositories |
| `GET /repositories/{repository_id}` | repository ID | repository detail |
| `PATCH /repositories/{repository_id}` | mutable fields + `expected_revision` | `200` updated repository |
| `DELETE /repositories/{repository_id}` | repository ID | `204`; guarded cascade |
| `POST /repositories/{repository_id}/index-jobs` | optional scan/app overrides | `202` job ID; `409` nếu writer bận |
| `GET /index-jobs/{job_id}` | job ID | stage, repository, progress revision, report, snapshot/error; `Retry-After: 1` khi chưa terminal. Không có ETag hay `If-None-Match` |
| `GET /repositories/{repository_id}/snapshots` | `offset`, `limit` | paged snapshots newest-first |
| `GET /repositories/{repository_id}/snapshots/{snapshot_id}` | owned IDs | snapshot metadata, metrics, capabilities |
| `POST /repositories/{repository_id}/snapshots/{snapshot_id}/activate` | owned IDs | `200` repository + active snapshot; không tạo job |
| `DELETE /repositories/{repository_id}/snapshots/{snapshot_id}` | owned IDs | `204`; guarded delete |
| `GET /technologies` | `snapshot_id` bắt buộc | xem Technology detection data flow |
| `GET /dependencies` | snapshot, subtype, q, page | dependency inventory/provenance |
| `GET /diagnostics` | snapshot + page | warnings/errors |
| `GET /entities` | snapshot, q/type/page | stable ordered search results |
| `GET /entities/{id}` | snapshot | metadata and evidence |
| `GET /subgraph` | snapshot/root/direction/edges/depth/budget | nodes, edges, limits |
| `POST /context` | bounded traversal request | context JSON |
| `POST /conversations` | snapshot + optional title | `201` conversation pin repository/snapshot |
| `GET /conversations` | optional repository/snapshot filter + page | conversation summaries |
| `GET /conversations/{id}/turns` | page | ordered persisted turns |
| `POST /conversations/{id}/turns` | question + required `client_request_id` and `expected_revision`; optional root | answer or clarification |
| `DELETE /conversations/{id}` | conversation ID | `204` |

Không duy trì alias `POST /index-jobs`, `GET /snapshot`, `GET /snapshots` hoặc
`POST /snapshot/activate` trong baseline chưa approve: các endpoint đó thiếu
repository ownership rõ ràng.

## Snapshot contract

Snapshot response gồm `snapshot_id`, `repository_id`, `source_revision` dạng
`manifest:<sha256>` của immutable local manifest, `manifest_hash`, `scan_config_digest`,
`analyzer_version`, `schema_version`, `adapter_versions`,
`status`, metrics/capabilities, `created_at` và `is_active`. Snapshot list order
`created_at DESC, snapshot_id ASC`.

Snapshot graph/manifest/source revision không có PATCH. Index thành công tạo row mới
và atomically đổi active pointer của repository. Activate chỉ đổi pointer. DELETE
active snapshot trả `409 snapshot_active`; reader hoặc conversation reference trả
`409 snapshot_in_use`. Repository DELETE trả `409 repository_busy` khi có job chưa
terminal và `409 repository_in_use` khi có reader/conversation; nếu hợp lệ, cascade
job/snapshot con trong một operation nhất quán.

## Shared limits

- Paging: default 20, maximum 100. Repository/snapshot order được định nghĩa ở trên;
  search order theo type, qualified name, ID.
- Traversal: BFS; direction `incoming|outgoing|both`; depth ≤6; nodes ≤200;
  edges ≤400; context characters 2.000–50.000.
- Question/model/query/timeout và history-window limits là normative trong
  `NFR-RKG-REL-001`; transport chỉ validate/report cùng effective values.

## CLI contract

- `rkg repository create|list|show|update|delete` gọi cùng application services,
  optimistic revision, redaction và delete guards với repository API.
- `rkg snapshot list|show|activate|delete --repository <id>` dùng cùng snapshot
  ownership/lifecycle semantics với API.
- `rkg index --repository <id>` dùng source/defaults đã đăng ký và
  cùng validation/error semantics với nested index endpoint; thành công trả exit `0`,
  validation/job failure trả exit `1`.
- `rkg serve` mặc định bind `127.0.0.1`, một application worker; bind non-loopback
  hoặc multi-worker bị từ chối trong MVP.
- CLI không in credential, session token hoặc absolute host path.

## Progress and streaming decision

API v1 dùng polling cho index jobs và bounded blocking response cho conversation
turns. Client phải honor `Retry-After` (guidance mặc định 1 giây khi active, backoff
tối đa 5 giây), dừng ở terminal state và cancel polling khi view unmount. Conversation
UI hiển thị `pending`; provider timeout theo Shared limits. SSE/WebSocket/token
streaming và xóa turn riêng lẻ ngoài phạm vi v1.

Compatible additions có thể thêm optional response fields. Xóa/đổi tên field, đổi
enum semantics hoặc endpoint behavior sau baseline cần `/api/v2`; security/error fix
giữ schema vẫn thuộc v1.

## Context request

```json
{
  "snapshot_id": "scan-001",
  "root_id": "api-order-detail",
  "direction": "outgoing",
  "edge_types": ["handled_by", "calls", "depends_on", "reads", "writes", "publishes", "consumes"],
  "depth": 4,
  "max_nodes": 50,
  "max_edges": 100,
  "max_chars": 20000
}
```

Response chứa `schema_version`, repository/snapshot/root, nodes, edges,
`diagnostic_summary`, `truncated` và `truncation_reasons`. Truncation giữ valid JSON,
root và referential integrity.

## Conversation turn response

Fields: `schema_version`, `conversation_id`, `turn_id`, `revision`, `repository_id`,
`snapshot_id`, `status`, `resolved_question`, `answer`, `claims`, `citations`,
`candidate_entities`, `limitations`, `retrieval_truncated`, `history_truncated`,
`context_turn_ids`, `usage`. Status là `answered`, `insufficient_evidence` hoặc
`needs_clarification`.

## Errors

Envelope: `{"error":{"code":"...","message":"..."}}`. Required semantics:

- `401`: invalid local session/Origin/Host;
- `404`: missing resource hoặc repository/snapshot ownership mismatch;
- `409`: `index_job_busy`, `repository_conflict`, `repository_busy`,
  `repository_in_use`, `snapshot_active`, `snapshot_in_use`,
  `conversation_conflict`, `conversation_busy` hoặc `no_active_snapshot`;
- `410 snapshot_unavailable`: snapshot metadata/reference còn biết nhưng graph payload
  mất ngoài lifecycle API; không dùng cho snapshot đã DELETE thành công;
- `422`: invalid budget/input, `repository_source_immutable`, missing required request
  identity/revision, source ngoài allowed roots hoặc question quá dài;
- `502` provider error; `503` LLM disabled; `504` provider timeout.

Messages không tiết lộ absolute host path, credential, source locator chưa redact hoặc
ownership của repository khác.

## Directory entities and historical snapshot compatibility

Target current-snapshot Entity.type values: Directory, SourceUnit, Type, Callable,
Endpoint, DataResource, MessageChannel, Configuration, ExternalDependency.
Repository remains the catalog resource/graph root, not a second Entity row.
GET /entities supports type=Directory. Detail/subgraph/context preserve stable ID,
relative path and absent line/kind fields. Module/package names are SourceUnit
attributes. Directory is a normal selectable/searchable graph entity.

New snapshots do not emit Namespace. Older snapshots may return/filter Namespace;
it is a legacy type, not an alias for Directory. Compatibility uses snapshot
analyzer/schema/adapter metadata, preserving historical context/citations. Structural
Evidence with RKG.structure.contains.v1 is relative-path provenance; its 1/1 marker
must not appear as syntax evidence or a source excerpt. API routes stay /api/v1 with
reads for both generations; the analyzer contract moves to v2. TASK-RKG-027 implements this behavior in the current tree; verification is recorded
in TEST-RKG-DIRECTORY-IMPLEMENTATION-001. Existing running server processes must
restart to load the new code. Evidence/context JSON marks provenance=filesystem
for structural references and provenance=source otherwise.

## Technology detection data flow

Detection trong adapter/selection được ghi vào `Job.report_json.technologies`
cùng `snapshot_id` sau publish. `GET /technologies` đọc row
`TechnologyDetection` theo `snapshot_id` nếu có, và trả evidence của các row đó.
Pipeline hiện tại không tạo row này. Khi bảng trống, response lấy technologies
trong `report_json` của job có cùng `snapshot_id`. Fallback đó không điền
evidence từ graph. Không mô tả bảng `TechnologyDetection` là đã được populate
bởi scan hiện tại.

`ScanFile` cùng trạng thái operational: schema và đường xóa có thật; không có
writer hiện tại.

## Framework documentation routes

`FastAPI()` mặc định phục vụ `/docs`, `/redoc` và `/openapi.json`. Session gate
chỉ chặn mutation dưới `/api/`. Ba route này là surface framework, không nằm
trong bảng endpoint v1 ở trên và không phải product contract được duyệt.

## Unverified FastAPI version extraction

Job report and snapshot capabilities may include executed `adapter_ids` and
`capabilities` while `support_state` remains `version_unverified`. These record
extraction of supported static syntax, not verified framework compatibility.
An `adapter_version_unverified` warning is included in the job and persisted
snapshot diagnostics. Known incompatible versions remain `unsupported_version`.

## Focused traversal request options

GET /subgraph and POST /context add view (neighborhood default, or flow),
include_structure (false default) and include_dependencies (false default). Unknown
view is invalid_request (422). In neighborhood, direction and edge_types retain their
existing behavior; `include_dependencies` does not remove edges there. In flow, root
type determines downstream/upstream direction and allowed semantic relation kinds;
edge_types can further narrow that set. `include_dependencies=false` omits
`depends_on` except when the root is `DataResource`, `MessageChannel`,
`Configuration`, or `ExternalDependency`: those upstream roots still include
`depends_on` edges of the root itself. `include_dependencies=true` adds
`depends_on` to the flow kind set for the nodes flow expands. Ownership
contains edges are an independent overlay when requested, not filtered by the semantic
edge list, and never seed semantic expansion. Files/directories/legacy Namespace roots
fall back to neighborhood. Node/edge budgets include the overlay; semantic depth does
not. Response shape and legacy clients remain compatible. Context export uses the same
policy before existing character truncation. SQLAlchemy may now record version_unverified
with executed adapters/capabilities and a warning, matching the opt-in FastAPI policy.

Subgraph responses acknowledge the requested profile with `view: flow|neighborhood`.
The live client requires `view: flow` for a flow request; an absent/mismatched
acknowledgement is surfaced as client error `graph_flow_unavailable`. This prevents
a running pre-flow backend from silently returning a neighborhood graph.

## Conversational usability L3 — CHG-RKG-2026-002

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

Question is nonblank after trimming, with no application character ceiling on the wire. Locale
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
depth 4/nodes 50/edges 100/chars 20000, with no default application model-call/graph-operation/token/deadline ceiling.

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
