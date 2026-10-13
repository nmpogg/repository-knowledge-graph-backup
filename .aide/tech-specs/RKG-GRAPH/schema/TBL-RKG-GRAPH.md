---
uid:
key: TBL-RKG-GRAPH
type: storage-schema
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 15
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  owned_by: [CMP-RKG-GRAPH]
  satisfies: [FR-RKG-001, FR-RKG-002, FR-RKG-003, FR-RKG-004, FR-RKG-005]
  constrained_by: [NFR-RKG-REL-001, NFR-RKG-SEC-001]
classification: internal
ai_assisted: true
---
# TBL-RKG-GRAPH - Kuzu graph and operational schema

> Owned by `CMP-RKG-GRAPH` — thư mục `tech-specs/RKG-GRAPH/schema/`.

## Node tables

`SchemaMeta`, `Repository`, `Snapshot`, `Entity`, `Evidence`, `Diagnostic`,
`ScanFile`, `Job`, `TechnologyDetection`, `ExternalDependency`, `Conversation`,
`Turn`.

`SchemaMeta` is a singleton physical-migration row (`id = "current"`, monotonic
`version`, `applied_at`). Application bootstrap/migrate owns it; it is not an API
resource. Migrations open a previous-schema fixture and retain relationships —
never drop the user database as an upgrade strategy.

Logical entity types: Repository, Directory, SourceUnit, Type, Callable, Endpoint,
DataResource, MessageChannel, Configuration, ExternalDependency. Physical `Repository` vừa là catalog row
bền vững vừa là graph root; các type còn lại nằm trong `Entity` theo snapshot.
Common entity fields gồm `id`, `repository_id`, `snapshot_id`, `type`, `name`,
`qualified_name`, relative `file_path`, lines, `language_kind`, `framework_kind` và
`attributes`. Tên cụ thể như module/class/function/table/topic là giá trị kind hoặc
attribute do adapter profile phát ra, không phải label mà core coordinator đóng cứng. Graph edges ngoài
`exposes` target generic `Entity` row. `ExternalDependency` là projection 1:1
inventory/provenance projection whose primary key equals the corresponding Entity ID;
it is not a second graph identity.

## Repository and snapshot lifecycle

- `Repository` stores immutable canonical source identity through an internal
  `source_locator` + `source_type` and a duplicate-detection hash. The internal
  locator is server-only; API/UI/log use `source_locator_redacted`. Mutable defaults
  use optimistic `revision`.
- `Repository.active_snapshot_id` is nullable and, when set, must reference a
  `Snapshot` with the same `repository_id`.
- `Snapshot` stores immutable `source_revision` derived from the local manifest,
  manifest/config digests and analyzer/schema/adapter versions. Re-index inserts a new row; it never
  updates graph/source identity of an existing row.
- `Job.repository_id`, `Snapshot.repository_id` and `Conversation.repository_id`
  must reference an existing Repository. Kùzu does not enforce these foreign keys;
  application services validate them in the same transaction as mutation.
- Snapshot delete removes snapshot-scoped Entity/Evidence/Diagnostic/Detection/
  dependency rows and relationships atomically only after active-reader/conversation/
  active-pointer guards. Repository delete additionally requires no non-terminal job
  and cascades only rows owned by that repository.

## Graph relationship tables (13)

| Type | Source → target |
|---|---|
| `contains` | Repository -> Directory/SourceUnit; Directory -> Directory/SourceUnit; SourceUnit/Type/Callable -> lexical Type/Callable |
| `imports` | SourceUnit -> source entity or ExternalDependency; module/package targets resolve to SourceUnits |
| `exposes` | Repository → Endpoint |
| `handled_by` | Endpoint → Callable |
| `calls` | Callable → Callable |
| `implements` | Type → declared abstraction Type |
| `inherits_from` | Type → direct base Type |
| `maps_to` | Type → DataResource |
| `reads`, `writes` | Callable or Type → DataResource (Type sources aggregate owned repository access for Java/JPA) |
| `publishes`, `consumes` | Callable → MessageChannel |
| `depends_on` | Endpoint/Callable/SourceUnit/Type/Repository → dependency target |

Every edge carries `snapshot_id`, rule and one or more evidence locations. Edge ID
hashes snapshot/type/source/target; multiple call sites are aggregated as evidence.
Physical `EXPOSES` is `FROM Repository TO Entity`. Physical `DEPENDS_ON` is
multi-FROM `FROM Repository TO Entity, FROM Entity TO Entity` so repository-rooted
`depends_on` facts use the same EXPOSES-style pattern; Kùzu 0.11.3 accepts the
union. If a future engine pin cannot, introduce a dedicated REL and record it in
a migration — do not invent a second graph identity for Repository.

Physical Kùzu DDL is the fenced block below. `DDL-RKG-GRAPH.cypher` is the
executable extract of that block and stays beside this file because
`approval-006` and schema tests pin the path. Revision 12 recorded operational
writer status without a shape change. Revision 13 adds only the nullable
Turn.response_metadata_json column; the target SchemaMeta version is 3. Current
application migration remains at version 2 until chatbot implementation tasks.
MIG-RKG-CHATBOT-v3 is the candidate version-2-to-3 migration, executed only on
isolated fixtures for Contract Gate evidence. Revision 15 keeps the adapter
edge sources and navigation Endpoint wording together with the revision 14
conversation-metadata contract. The physical DDL shape is unchanged from
revision 14.

`ScanFile` and `TechnologyDetection` are created by DDL. Current application
code deletes them by `job_id` or `snapshot_id` and does not insert them.
A scan does not populate those tables. Technology results used by
`GET /technologies` come from `Job.report_json` unless `TechnologyDetection`
rows already exist. `ExternalDependency` rows are written during publish.
The pre-chatbot application SchemaMeta.version is 2. TASK-RKG-027 implements an atomic v1-to-v2
CONTAINS migration preserving historical snapshots and relationships. Execution
and regression results are recorded in TEST-RKG-DIRECTORY-IMPLEMENTATION-001.
Its schema must be executed against the
version pinned by `TASK-RKG-001` before Contract Gate approval; this Markdown file
remains the semantic source of truth if a generated migration diverges.

Domain `Entity.id` is stable across snapshots (no snapshot in the hash). Kùzu node
tables require a single-column primary key, so the physical `Entity.id` /
`ExternalDependency.id` stored for a published snapshot is the snapshot-qualified
encoding `{snapshot_id}:{domain_id}`. Application services encode on write and
decode on read; API/CLI continue to expose the domain ID. Edge endpoint
properties stored on relationships use the same physical keys when the endpoint
is an `Entity` (Repository endpoints stay the catalog `Repository.id`).

## Search and data-minimization constraints

- MVP search filters `snapshot_id` first, then normalized `name`, `qualified_name`, Endpoint
  method and path with stable type/name/ID ordering. At the bounded graph size, no
  secondary-index dependency is assumed; add a version-supported index only after the
  NFR benchmark shows need and record it in a migration.
- Configuration stores only key identity/kind/owner and evidence. A value field does
  not exist in the physical schema; GraphValidator rejects value-like attributes.
- Operational `Job`/`Diagnostic` data and redacted `Conversation`/`Turn` data are
  separate from graph facts. Operational logs never duplicate question/answer text.

## Identity

- `repository_id` identifies one registered source and survives all scans until repository delete.
- `snapshot_id` identifies one successfully published graph.
- Source entity ID hashes repository, relative path, type and qualified name; line
  number is not normally part of identity.
- DataResource: repository + resource kind + namespace + adapter identity fields;
  MessageChannel: repository + channel kind + namespace + name; Configuration:
  repository + kind + owner + key.
- GraphValidator rejects missing or cross-snapshot endpoints.
- Repository/snapshot application services reject cross-repository ownership before
  reads, activate or delete; mismatch is not reported in a way that leaks ownership.
- `Evidence.rule` và edge `rule` phải là ID có version từ rule registry của analyzer
  (dạng `RKG.<family>.<name>.v<integer>`); giá trị rỗng/ad-hoc bị GraphValidator từ chối.

## Conversation constraints

Conversation stores repository/snapshot/title/revision/timestamps/structured state.
Turn stores sequence, request identity/hash, question/resolution/status/answer,
claims/citations/context turn IDs/usage/error/timestamps. Unique key:
`(conversation_id, client_request_id)`; physical `Turn.id` is
`"turn_" + hex(sha256(utf8(conversation_id + ":" + client_request_id)))` (toàn bộ 64
hex characters). DDL primary key trên `Turn.id` enforce uniqueness; application phải
kiểm tra cùng business key nhưng khác `request_hash` là conflict, không được overwrite.
No chain-of-thought or question/answer text in operational logs.

Conversation creation derives `repository_id` from the selected Snapshot and rejects
any supplied/derived mismatch. Repository or snapshot deletion is blocked while a
Conversation references it; deleting a Conversation releases that reference.

## Migration rule

Migrations must open a fixture from the previous schema and retain relationships.
Never drop the user's database as an upgrade strategy.

## Directory and language scope contract (revision 10)

| Logical type | Role | Producer |
|---|---|---|
| Repository | Registered project and persistent graph root | Repository lifecycle service |
| Directory | Repository-relative filesystem directory | Core analyzer structure builder |
| SourceUnit | Source file/unit | Language adapter |
| Type | Declared class/interface or other supported type | Language adapter |
| Callable | Supported function/method/constructor | Language adapter |
| Endpoint | HTTP API entrypoint (method+path, may `exposes`) or UI navigation route (`kind=navigation`, `framework_kind` e.g. react-router, no HTTP method, no API `exposes`; OQ-RKG-007) | Framework adapter |
| DataResource | Data resource such as a table | Data-access adapter |
| MessageChannel | Message topic/queue | Messaging adapter |
| Configuration | Configuration key identity, never its value | Applicable adapter |
| ExternalDependency | External library/service identity | Applicable adapter |

- New snapshots use Directory instead of Namespace nodes. Namespace is a legacy
  snapshot type, not an alias for Directory. Module/package scope stays in the
  symbol index and qualified names. SourceUnit attributes carry `module_name`
  or `package_name` as documented by the language profile.
- Core creates one Directory for each ancestor of emitted SourceUnit.file_path,
  deduplicated by repository-relative POSIX path, without a second filesystem walk.
  Empty directories and directories without an emitted SourceUnit are omitted.
  Repository represents the root; no Directory named `.` is emitted. Paths stay
  relative to the canonical repository root even for source_root scans; intermediate
  ancestors are derived from paths, never scanned outside the selected scope.
- Directory.name is the final path component. Directory.qualified_name and
  Directory.file_path are the full relative directory path without trailing slash.
  Line fields, language_kind and framework_kind are absent. Stable ID follows
  source_entity_id(repository, relative path, Directory, relative path).
- Core adds Repository/Directory containment. Adapters add SourceUnit -> top-level
  Type/Callable and nested lexical containment. Directory is not an import target.
  Java overloads require distinct qualified identities/signatures in a future Java
  profile; the core does not rewrite adapter names or deduplicate by name alone.
- Structural contains edges use `RKG.structure.contains.v1`. Each has a deterministic
  witness: the lexicographically first emitted descendant SourceUnit path backed
  by the frozen manifest. Evidence uses this relative file path and lines 1/1 as
  a path-provenance marker, including empty files. This does not claim a source
  statement exists. Validation checks manifest membership and ancestor/child paths.
  API/context mark this evidence with provenance=filesystem (other evidence uses
  provenance=source). UI displays relative paths without line markers or excerpts.
  Other edges keep their syntax-evidence rules. Directory nodes themselves have no
  line range; their evidence is obtained from structural edges.
- Physical CONTAINS must support Repository -> Entity and Entity -> Entity.
  Directory remains an Entity row; no new node table is needed. The relationship
  migration retains all historical relationships and snapshots.
- Old Namespace snapshots, IDs and conversation references remain immutable/readable.
  API/UI compatibility uses snapshot analyzer/schema/adapter metadata. Re-index
  creates a new Directory snapshot; it does not relabel old Namespace nodes,
  rewrite historical counts, or automatically re-index repositories.

## Physical DDL

The fenced statements are the normative physical shape for this revision.
`DDL-RKG-GRAPH.cypher` is the executable extract and must match this block.
`approval-006` pinned an earlier extract of the revision 9/11 shape; it does
not approve revision 12.

```cypher
// DDL-RKG-GRAPH — physical bootstrap for TBL-RKG-GRAPH revision 12.
// Table shape is unchanged from revision 11. Revision 12 records that ScanFile
// and TechnologyDetection have delete paths and no current writer.
// Execute this file against the Kùzu version pinned by TASK-RKG-001 before Contract Gate.
// Semantic names exposed by API remain lowercase even though physical tables are uppercase.
// Evidence/edge rule strings use versioned IDs RKG.<family>.<name>.v<integer> and are
// validated before publication; Kùzu does not enforce this enum in the DDL.
// SchemaMeta.version is the physical migration counter; never drop the user DB to upgrade.
// DEPENDS_ON uses multi-FROM (Repository|Entity → Entity) to match TBL/domain EXPOSES pattern.

CREATE NODE TABLE SchemaMeta(
  id STRING PRIMARY KEY,
  version INT64,
  applied_at TIMESTAMP
);

CREATE NODE TABLE Repository(
  id STRING PRIMARY KEY,
  revision INT64,
  display_name STRING,
  source_type STRING,
  source_locator STRING,
  source_identity_hash STRING,
  source_locator_redacted STRING,
  source_root STRING,
  app_module STRING,
  app_symbol STRING,
  scan_defaults_json STRING,
  active_snapshot_id STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE NODE TABLE Snapshot(
  id STRING PRIMARY KEY,
  repository_id STRING,
  source_revision STRING,
  manifest_hash STRING,
  scan_config_digest STRING,
  analyzer_version STRING,
  schema_version STRING,
  adapter_versions_json STRING,
  status STRING,
  created_at TIMESTAMP
);

CREATE NODE TABLE Entity(
  id STRING PRIMARY KEY,
  repository_id STRING,
  snapshot_id STRING,
  type STRING,
  name STRING,
  qualified_name STRING,
  file_path STRING,
  start_line INT64,
  end_line INT64,
  language_kind STRING,
  framework_kind STRING,
  attributes_json STRING
);

CREATE NODE TABLE Evidence(
  id STRING PRIMARY KEY,
  snapshot_id STRING,
  file_path STRING,
  start_line INT64,
  end_line INT64,
  rule STRING
);

CREATE NODE TABLE Diagnostic(
  id STRING PRIMARY KEY,
  job_id STRING,
  snapshot_id STRING,
  severity STRING,
  code STRING,
  file_path STRING,
  line INT64,
  message STRING
);

CREATE NODE TABLE ScanFile(
  id STRING PRIMARY KEY,
  job_id STRING,
  relative_path STRING,
  content_hash STRING,
  status STRING,
  diagnostic_count INT64
);

CREATE NODE TABLE Job(
  id STRING PRIMARY KEY,
  repository_id STRING,
  status STRING,
  stage STRING,
  source_type STRING,
  manifest_hash STRING,
  report_json STRING,
  error_code STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE NODE TABLE TechnologyDetection(
  id STRING PRIMARY KEY,
  job_id STRING,
  snapshot_id STRING,
  technology STRING,
  version_constraint STRING,
  support_state STRING,
  evidence_ids STRING[]
);

CREATE NODE TABLE ExternalDependency(
  id STRING PRIMARY KEY,
  snapshot_id STRING,
  kind STRING,
  name STRING,
  version_constraint STRING,
  provenance_json STRING,
  origin STRING
);

CREATE NODE TABLE Conversation(
  id STRING PRIMARY KEY,
  repository_id STRING,
  snapshot_id STRING,
  title STRING,
  revision INT64,
  state_json STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

// Turn.id = "turn_" + full lowercase hex SHA-256 of UTF-8
// (conversation_id + ":" + client_request_id); application validates request_hash conflicts.
CREATE NODE TABLE Turn(
  id STRING PRIMARY KEY,
  conversation_id STRING,
  sequence INT64,
  client_request_id STRING,
  request_hash STRING,
  question STRING,
  resolved_question STRING,
  status STRING,
  answer STRING,
  claims_json STRING,
  citations_json STRING,
  context_turn_ids STRING[],
  usage_json STRING,
  response_metadata_json STRING,
  error_code STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE REL TABLE EXPOSES(FROM Repository TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE CONTAINS(FROM Repository TO Entity, FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE IMPORTS(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE HANDLED_BY(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE CALLS(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE IMPLEMENTS(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE INHERITS_FROM(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE MAPS_TO(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE READS(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE WRITES(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE PUBLISHES(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE CONSUMES(FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
CREATE REL TABLE DEPENDS_ON(FROM Repository TO Entity, FROM Entity TO Entity, edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]);
```

## Conversation metadata and pending intent — CHG-RKG-2026-002

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
| question | Original redacted, trimmed business question, no character ceiling; never the ordinal reply. Exclude this text from the structural state byte bound |
| ui_locale / language | Normalized original fallback locale and effective answer language, vi/en |
| relation_types | Unique allowed graph relation names, stable order |
| direction | incoming or outgoing from resolved intent |
| entity_type | Canonical query type or any |
| candidate_ids | Ordered unique domain IDs, ≤20, exactly equal to pending_candidate_ids |

The enclosing conversation pin supplies repository/snapshot ownership; no mutable
pin is duplicated in this JSON. State remains redacted; the structural envelope
excluding pending_intent.question is ≤32768 UTF-8 bytes. The original question
is not truncated or limited by this envelope bound. Old state lacking state_version/pending_intent remains readable;
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
