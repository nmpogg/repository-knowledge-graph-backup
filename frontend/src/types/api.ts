/** Contract-shaped types aligned with API-RKG-CORE-v1 / UIS-RKG-001. */

export type SourceType = 'local'

export type JobStage =
  | 'queued'
  | 'detecting'
  | 'indexing'
  | 'succeeded'
  | 'succeeded_with_warnings'
  | 'failed'

export type SupportState =
  | 'supported_patterns'
  | 'detected_only'
  | 'version_unverified'
  | 'unsupported_version'

export type EdgeDirection = 'incoming' | 'outgoing' | 'both'

export type EdgeType =
  | 'handled_by'
  | 'calls'
  | 'depends_on'
  | 'reads'
  | 'writes'
  | 'publishes'
  | 'consumes'
  | 'implements'
  | 'inherits_from'
  | 'contains'
  | 'imports'
  | 'exposes'
  | 'maps_to'

export type EntityType =
  | 'directory'
  | 'file'
  | 'module'
  | 'class'
  | 'function'
  | 'endpoint'
  | 'table'
  | 'topic'
  | 'config'
  | 'interface'
  | 'dependency'

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}

export interface PageMeta {
  offset: number
  limit: number
  total: number
}

export interface ScanDefaults {
  include_globs?: string[]
  exclude_globs?: string[]
  max_files?: number
}

export interface Repository {
  repository_id: string
  revision: number
  display_name: string
  source_type: SourceType
  source_locator_redacted: string
  source_root?: string | null
  app_module?: string | null
  app_symbol?: string | null
  scan_defaults?: ScanDefaults | null
  active_snapshot_id: string | null
  created_at: string
  updated_at: string
}

export interface RepositoryCreateBody {
  display_name: string
  source_type: SourceType
  path: string
  source_root?: string
  app_module?: string
  app_symbol?: string
  scan_defaults?: ScanDefaults
}

/** PATCH body — source identity is immutable; expected_revision is required. */
export interface RepositoryUpdateBody {
  expected_revision: number
  display_name?: string
  source_root?: string
  app_module?: string | null
  app_symbol?: string | null
  scan_defaults?: ScanDefaults | null
}

export interface Snapshot {
  snapshot_id: string
  repository_id: string
  source_revision: string
  manifest_hash: string
  scan_config_digest: string
  analyzer_version: string
  schema_version: string
  adapter_versions: Record<string, string>
  status: 'ready' | 'unavailable'
  metrics: {
    entity_count: number
    edge_count: number
    warning_count: number
  }
  capabilities: {
    technologies: string[]
    graph_ready: boolean
  }
  created_at: string
  is_active: boolean
}

export interface AppCandidate {
  candidate_id: string
  module: string
  symbol: string
  evidence: string
}

export interface JobReport {
  summary: string
  warnings: string[]
  app_candidates?: AppCandidate[]
  selected_app_id?: string | null
  technologies?: Array<{ technology: string; support_state: SupportState }>
}

export interface IndexJob {
  job_id: string
  repository_id: string
  stage: JobStage
  progress_revision: number
  message: string
  report?: JobReport | null
  snapshot_id?: string | null
  error?: { code: string; message: string } | null
  updated_at: string
  retry_after_seconds?: number
}

export interface EvidenceRef {
  provenance?: 'filesystem' | 'source'
  relative_path: string
  start_line: number
  end_line?: number
  excerpt?: string
}

export interface EntitySummary {
  scope_name?: string
  id: string
  type: EntityType
  name: string
  qualified_name: string
  summary?: string
  file_path?: string
  /** 1-based source line where this entity starts in file_path. */
  start_line?: number
  /** 1-based source line where this entity ends in file_path. */
  end_line?: number
  /** Raw entity attributes (method/path/kind=navigation, …). */
  attributes?: Record<string, string>
}

export interface EntityDetail extends EntitySummary {
  snapshot_id: string
  evidence: EvidenceRef[]
  metadata: Record<string, string>
}

export interface GraphNode {
  id: string
  type: EntityType
  label: string
  qualified_name: string
  file_path?: string
  location?: string
  /** Optional entity attributes (http_requests on FE callables, kind on endpoints). */
  attributes?: Record<string, string>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: EdgeType
  label: string
}

export interface SubgraphResponse {
  view?: 'flow' | 'neighborhood'
  snapshot_id: string
  root_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  truncated: boolean
  truncation_reasons: string[]
  limits: {
    depth: number
    max_nodes: number
    max_edges: number
  }
}

export interface TechnologyDetection {
  technology: string
  version?: string | null
  support_state: SupportState
  evidence: EvidenceRef[]
  limitations: string[]
}

export interface DependencyItem {
  id: string
  name: string
  version?: string | null
  subtype: 'declared' | 'imported' | 'usage'
  provenance: 'declared' | 'imported' | 'usage'
  evidence: EvidenceRef[]
}

export interface DiagnosticItem {
  id: string
  severity: 'warning' | 'error' | 'info'
  code: string
  message: string
  evidence?: EvidenceRef[]
}

export interface ContextRequest {
  snapshot_id: string
  root_id: string
  direction: EdgeDirection
  edge_types: EdgeType[]
  depth: number
  max_nodes: number
  max_edges: number
  max_chars: number
  view?: 'flow' | 'neighborhood'
  include_structure?: boolean
  include_dependencies?: boolean
}

export interface ContextExport {
  schema_version: string
  repository_id: string
  snapshot_id: string
  root_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  diagnostic_summary: string[]
  truncated: boolean
  truncation_reasons: string[]
}

export type ConversationTurnStatus =
  | 'pending'
  | 'answered'
  | 'needs_clarification'
  | 'insufficient_evidence'
  | 'failed'
  | 'interrupted'

export interface ConversationSummary {
  conversation_id: string
  repository_id: string
  snapshot_id: string
  title: string
  revision: number
  focus_entity_id: string | null
  created_at: string
  updated_at: string
}

export interface ConversationCreateBody {
  repository_id: string
  snapshot_id?: string
  title?: string
}

export interface Claim {
  citation_indexes?: number[]
  text: string
  edge_id?: string
}

export interface Citation {
  edge_id?: string
  snapshot_id: string
  entity_id?: string
  evidence_id?: string
  quote?: string
}

export interface TurnUsage {
  input_tokens?: number
  output_tokens?: number
  model_calls?: number
}

export interface ConversationTurn {
  response_metadata?: ResponseMetadata | null
  turn_id: string
  sequence: number
  status: ConversationTurnStatus
  question: string
  resolved_question: string | null
  answer: string | null
  claims: Claim[]
  citations: Citation[]
  context_turn_ids: string[]
  error_code: string | null
}

export interface ConversationHistory {
  snapshot_available?: boolean
  conversation: ConversationSummary
  turns: Paged<ConversationTurn>
  candidate_entities: EntitySummary[]
}

export interface TurnSubmitBody {
  ui_locale?: "vi" | "en" | null
  question: string
  client_request_id: string
  expected_revision: number
  root_id?: string
}

export interface TurnSubmitResult extends ConversationTurn {
  schema_version: string
  conversation_id: string
  revision: number
  repository_id: string
  snapshot_id: string
  candidate_entities: EntitySummary[]
  limitations: string[]
  retrieval_truncated: boolean
  history_truncated: boolean
  usage: TurnUsage | null
}

export interface Paged<T> {
  items: T[]
  page: PageMeta
}

export class RkgApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'RkgApiError'
    this.status = status
    this.code = code
  }
}

export interface ResponseMetadata {
  version: 1
  language: 'vi' | 'en'
  kind: 'answer' | 'clarification' | 'greeting' | 'insufficient' | 'error'
  subject: { entity_id: string; type: string; name: string; qualified_name: string; method: string | null; path: string | null } | null
  coverage: 'complete' | 'partial' | 'unknown' | 'not_applicable'
  retrieval_truncated: boolean | null
  history_truncated: boolean | null
  limitations: string[]
  insufficient_reason: string | null
}

export interface ConversationCapabilities {
  schema_version: 'rkg.conversation-capabilities/1'
  features: string[]
  provider_enabled: boolean
}

export interface ExactCitation {
  schema_version: 'rkg.citation/1'
  conversation_id: string
  turn_id: string
  snapshot_id: string
  citation_index: number
  evidence: { id: string; file_path: string; provenance: 'source' | 'filesystem'; start_line: number | null; end_line: number | null; rule: string }
}
