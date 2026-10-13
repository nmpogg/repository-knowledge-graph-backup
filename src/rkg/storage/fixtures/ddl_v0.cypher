// Previous physical schema (T-001 / TBL revision 8 bootstrap).
// Used only as a migration fixture — never drop a user database to upgrade.
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
  error_code STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
CREATE REL TABLE EXPOSES(
  FROM Repository TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE CONTAINS(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE IMPORTS(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE HANDLED_BY(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE CALLS(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE IMPLEMENTS(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE INHERITS_FROM(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE MAPS_TO(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE READS(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE WRITES(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE PUBLISHES(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE CONSUMES(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
CREATE REL TABLE DEPENDS_ON(
  FROM Entity TO Entity,
  edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[]
);
