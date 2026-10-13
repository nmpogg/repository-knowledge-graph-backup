// CHG-RKG-2026-003: TBL revision14 widens pending question text only; physical table shape and SchemaMeta.version3 stay unchanged.
// DDL-RKG-GRAPH — physical bootstrap for TBL-RKG-GRAPH revision 15.
// Artifact revision: 15. Candidate SchemaMeta version 3; Kuzu 0.11.3. Target bootstrap must record version 3.
// Adds only nullable Turn.response_metadata_json; graph tables/relationships stay unchanged.
// Existing version-2 databases use MIG-RKG-CHATBOT-v3, never bootstrap over live data.
// Executed on isolated fixtures before Contract Gate; production integration is pending.
// Semantic edge names remain lowercase; operational transcripts are not log/evidence payloads.

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
