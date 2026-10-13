import { readResponseMetadata } from '../../pages/conversations/responseMetadata'
import type {
  Citation,
  Claim,
  ContextExport,
  ConversationHistory,
  ConversationSummary,
  ConversationTurn,
  ConversationTurnStatus,
  DependencyItem,
  DiagnosticItem,
  EdgeType,
  EntityDetail,
  EntitySummary,
  EntityType,
  GraphEdge,
  GraphNode,
  IndexJob,
  JobReport,
  JobStage,
  Paged,
  Repository,
  Snapshot,
  SubgraphResponse,
  SupportState,
  TechnologyDetection,
  TurnSubmitResult,
  TurnUsage,
} from '../../types/api'

/** Domain enum on the wire → labels the M0 screens already render. */
const DOMAIN_ENTITY: Record<string, EntityType> = {
  Directory: 'directory',
  SourceUnit: 'file',
  Namespace: 'module',
  Type: 'class',
  Callable: 'function',
  Endpoint: 'endpoint',
  DataResource: 'table',
  MessageChannel: 'topic',
  Configuration: 'config',
  ExternalDependency: 'dependency',
}

const UI_ENTITY: Record<string, string> = {
  directory: 'Directory',
  file: 'SourceUnit',
  module: 'Namespace',
  class: 'Type',
  function: 'Callable',
  endpoint: 'Endpoint',
  table: 'DataResource',
  topic: 'MessageChannel',
  config: 'Configuration',
  dependency: 'ExternalDependency',
}

const UI_TYPES = new Set<string>([
  'directory',
  'file',
  'module',
  'class',
  'function',
  'endpoint',
  'table',
  'topic',
  'config',
  'interface',
  'dependency',
])

const EDGE_TYPES = new Set<string>([
  'handled_by',
  'calls',
  'depends_on',
  'reads',
  'writes',
  'publishes',
  'consumes',
  'implements',
  'inherits_from',
  'contains',
  'imports',
  'exposes',
  'maps_to',
])

const SUPPORT_STATES = new Set<string>([
  'supported_patterns',
  'detected_only',
  'version_unverified',
  'unsupported_version',
])

const UI_STAGES = new Set<JobStage>([
  'queued',
  'detecting',
  'indexing',
  'succeeded',
  'succeeded_with_warnings',
  'failed',
])

const MESSAGES: Record<string, string> = {
  unauthorized: 'Phiên làm việc cục bộ không hợp lệ.',
  not_found: 'Không tìm thấy.',
  generic_not_found: 'Không tìm thấy.',
  invalid_request: 'Dữ liệu gửi lên không hợp lệ.',
  invalid_input: 'Dữ liệu gửi lên không hợp lệ.',
  source_path_invalid: 'Đường dẫn là bắt buộc và phải là đường dẫn cục bộ.',
  source_not_found:
    'Đường dẫn không tồn tại trên máy chủ RKG. Việc đăng ký không sửa hệ thống tệp của bạn.',
  source_outside_allowed_roots:
    'Đường dẫn nằm ngoài vùng cục bộ được phép. Hãy chọn đường dẫn trong vùng cho phép.',
  source_root_not_found: 'Thư mục nguồn con không tồn tại trong kho mã đã đăng ký.',
  source_link_escape: 'Đường dẫn vượt ra ngoài thư mục đã đăng ký.',
  source_config_invalid: 'Cấu hình vùng cục bộ được phép không hợp lệ.',
  repository_conflict: 'Xung đột kho mã. Hãy tải lại rồi thử lại.',
  repository_busy: 'Kho mã đang có việc lập chỉ mục chưa xong.',
  repository_in_use: 'Kho mã còn lượt đọc hoặc hội thoại đang tham chiếu.',
  repository_source_immutable: 'Định danh nguồn không đổi sau khi tạo kho mã.',
  snapshot_active: 'Không xóa được snapshot đang được chọn.',
  snapshot_in_use: 'Snapshot còn lượt đọc hoặc hội thoại đang tham chiếu.',
  snapshot_unavailable: 'Snapshot không dùng được. Hãy lập chỉ mục lại từ trang chi tiết kho mã.',
  no_active_snapshot: 'Kho mã chưa có snapshot đang dùng. Hãy lập chỉ mục hoặc kích hoạt một snapshot.',
  index_job_busy: 'Đang có một việc lập chỉ mục khác chạy.',
  app_selection_required: 'Chọn điểm vào ứng dụng để tiếp tục.',
  conversation_conflict: 'Hội thoại đã đổi. Hãy tải lại rồi xem lại câu hỏi.',
  conversation_busy: 'Hội thoại đang có lượt hỏi chưa xong.',
  invalid_turn_request: 'Câu hỏi hoặc mã phiên bản không hợp lệ.',
  llm_disabled: 'Nhà cung cấp mô hình chưa được cấu hình.',
  llm_timeout: 'Nhà cung cấp mô hình quá thời gian.',
  llm_provider_error: 'Nhà cung cấp mô hình trả lỗi.',
  llm_malformed_response: 'Nhà cung cấp mô hình trả kết quả không dùng được.',
  llm_budget_exceeded: 'Lượt hỏi vượt ngân sách mô hình.',
  provider_failed: 'Nhà cung cấp mô hình trả lỗi.',
  invalid_provider_status: 'Nhà cung cấp mô hình trả trạng thái không hợp lệ.',
}

/** UI search type → domain enum. `interface` has no domain type. */
export function domainEntityType(uiType: string | undefined): string | undefined {
  if (!uiType) return undefined
  if (uiType === 'interface') return undefined
  return UI_ENTITY[uiType] ?? uiType
}

export function uiEntityType(value: unknown): EntityType {
  const text = String(value ?? '')
  if (DOMAIN_ENTITY[text]) return DOMAIN_ENTITY[text]
  if (UI_TYPES.has(text)) return text as EntityType
  return 'module'
}

export function safePath(value: unknown): string {
  const text = String(value ?? '').replace(/\\/g, '/')
  if (!text) return ''
  const absolute = /^[a-zA-Z]:\//.test(text) || text.startsWith('/')
  if (!absolute) return text.replace(/^\/+/, '')
  const parts = text.split('/').filter(Boolean)
  return parts.slice(-2).join('/')
}

export function safeMessage(code: string, raw: string | undefined): string {
  const known = MESSAGES[code]
  if (known) return known
  const text = (raw ?? code).trim()
  if (/[a-zA-Z]:[\\/]|\\\\/.test(text)) return 'Yêu cầu không hợp lệ.'
  return text || 'Yêu cầu không hợp lệ.'
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {}
}

function stringMap(value: unknown): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [key, item] of Object.entries(record(value))) {
    if (item == null) continue
    out[key] = typeof item === 'string' ? item : JSON.stringify(item)
  }
  return out
}

export function mapPage<T>(raw: unknown, mapItem: (item: unknown) => T): Paged<T> {
  const body = record(raw)
  const nested = record(body.page)
  const offset = Number(nested.offset ?? body.offset ?? 0)
  const limit = Number(nested.limit ?? body.limit ?? 20)
  const total = Number(nested.total ?? body.total ?? 0)
  const items = Array.isArray(body.items) ? body.items.map(mapItem) : []
  return { items, page: { offset, limit, total } }
}

export function mapRepository(raw: unknown): Repository {
  const body = record(raw)
  return {
    repository_id: String(body.repository_id ?? ''),
    revision: Number(body.revision ?? 0),
    display_name: String(body.display_name ?? ''),
    source_type: 'local',
    source_locator_redacted: String(body.source_locator_redacted ?? ''),
    source_root: (body.source_root as string | null | undefined) ?? null,
    app_module: (body.app_module as string | null | undefined) ?? null,
    app_symbol: (body.app_symbol as string | null | undefined) ?? null,
    scan_defaults: (body.scan_defaults as Repository['scan_defaults']) ?? null,
    active_snapshot_id: (body.active_snapshot_id as string | null) ?? null,
    created_at: String(body.created_at ?? ''),
    updated_at: String(body.updated_at ?? ''),
  }
}

export function mapSnapshot(raw: unknown): Snapshot {
  const body = record(raw)
  const metrics = record(body.metrics)
  const capabilities = record(body.capabilities)
  return {
    snapshot_id: String(body.snapshot_id ?? ''),
    repository_id: String(body.repository_id ?? ''),
    source_revision: String(body.source_revision ?? ''),
    manifest_hash: String(body.manifest_hash ?? ''),
    scan_config_digest: String(body.scan_config_digest ?? ''),
    analyzer_version: String(body.analyzer_version ?? ''),
    schema_version: String(body.schema_version ?? ''),
    adapter_versions: stringMap(body.adapter_versions),
    status: body.status === 'unavailable' ? 'unavailable' : 'ready',
    metrics: {
      entity_count: Number(metrics.entity_count ?? 0),
      edge_count: Number(metrics.edge_count ?? 0),
      warning_count: Number(metrics.warning_count ?? 0),
    },
    capabilities: {
      technologies: Array.isArray(capabilities.technologies)
        ? capabilities.technologies.map(String)
        : [],
      graph_ready: Boolean(capabilities.graph_ready),
    },
    created_at: String(body.created_at ?? ''),
    is_active: Boolean(body.is_active),
  }
}

function mapStage(value: string): JobStage {
  if (UI_STAGES.has(value as JobStage)) return value as JobStage
  if (value === 'scanning' || value === 'detecting') return 'detecting'
  if (value === 'parsing' || value === 'extracting' || value === 'publishing') {
    return 'indexing'
  }
  return 'indexing'
}

function supportState(value: unknown): SupportState {
  const text = String(value ?? '')
  if (SUPPORT_STATES.has(text)) return text as SupportState
  return 'detected_only'
}

function mapCandidate(raw: unknown): JobReport['app_candidates'] {
  if (!Array.isArray(raw)) return undefined
  return raw.map((item) => {
    if (typeof item === 'string') {
      const [module, ...rest] = item.split(':')
      return {
        candidate_id: item,
        module: module || item,
        symbol: rest.join(':') || item,
        evidence: item,
      }
    }
    const body = record(item)
    const reference = String(body.reference ?? body.candidate_id ?? '')
    const [module, ...rest] = reference.split(':')
    const path = safePath(body.relative_path ?? body.evidence)
    const line = body.line == null ? '' : `:${String(body.line)}`
    return {
      candidate_id: reference,
      module: String(body.module ?? module ?? reference),
      symbol: String(body.symbol ?? (rest.join(':') || reference)),
      evidence: path ? `${path}${line}` : reference,
    }
  })
}

function jobSummary(report: Record<string, unknown>): string {
  if (typeof report.summary === 'string') return report.summary
  const files = record(report.files)
  if (Object.keys(files).length > 0) {
    return `Xét ${String(files.considered ?? 0)} tệp, phân tích ${String(files.parsed ?? 0)}, bỏ qua ${String(files.skipped ?? 0)}, lỗi ${String(files.errors ?? 0)}.`
  }
  return ''
}

function jobWarnings(report: Record<string, unknown>): string[] {
  if (Array.isArray(report.warnings)) return report.warnings.map(String)
  if (!Array.isArray(report.diagnostics)) return []
  return report.diagnostics.map((item) => {
    const body = record(item)
    return String(body.message ?? body.code ?? '')
  }).filter(Boolean)
}

function mapReport(raw: unknown): JobReport | null {
  if (!raw || typeof raw !== 'object') return null
  const report = record(raw)
  const technologies = Array.isArray(report.technologies)
    ? report.technologies.map((item) => {
        const body = record(item)
        return {
          technology: String(body.technology ?? ''),
          support_state: supportState(body.support_state),
        }
      })
    : []
  const selected = report.selected_application ?? report.selected_app_id ?? null
  return {
    summary: jobSummary(report),
    warnings: jobWarnings(report),
    app_candidates: mapCandidate(
      report.application_candidates ?? report.app_candidates,
    ),
    selected_app_id: selected == null ? null : String(selected),
    technologies,
  }
}

export function mapJob(raw: unknown, retryAfterHeader: string | null): {
  job: IndexJob
  retryAfter?: number
} {
  const body = record(raw)
  const report = mapReport(body.report)
  const errorBody = record(body.error)
  const errorCode = String(errorBody.code ?? record(body.report).error_code ?? '')
  const needsApp =
    errorCode === 'app_selection_required' &&
    (report?.app_candidates?.length ?? 0) > 0
  const stage = needsApp ? 'detecting' : mapStage(String(body.stage ?? body.status ?? ''))
  const error =
    needsApp || !errorBody.code
      ? null
      : { code: String(errorBody.code), message: safeMessage(String(errorBody.code), String(errorBody.message ?? '')) }
  const terminal = ['succeeded', 'succeeded_with_warnings', 'failed'].includes(stage)
  const parsed = Number(retryAfterHeader)
  const retryAfter = terminal
    ? undefined
    : Number.isFinite(parsed) && parsed > 0
      ? parsed
      : needsApp
        ? 5
        : 1
  const message = needsApp
    ? MESSAGES.app_selection_required
    : stage === 'failed' && error
      ? error.message
      : stage === 'succeeded'
        ? 'Lập chỉ mục thành công'
        : stage === 'succeeded_with_warnings'
          ? 'Lập chỉ mục xong, có cảnh báo'
          : stage === 'indexing'
            ? 'Đang lập chỉ mục mã nguồn và dựng đồ thị'
            : stage === 'detecting'
              ? 'Đang phát hiện ứng dụng và adapter'
              : 'Job đã vào hàng đợi'
  return {
    job: {
      job_id: String(body.job_id ?? ''),
      repository_id: String(body.repository_id ?? ''),
      stage,
      progress_revision: Number(body.progress_revision ?? 0),
      message: message || jobSummary(record(body.report)),
      report,
      snapshot_id: (body.snapshot_id as string | null) ?? null,
      error,
      updated_at: String(body.updated_at ?? ''),
      retry_after_seconds: retryAfter,
    },
    retryAfter,
  }
}

function evidenceList(raw: unknown, fallback?: Record<string, unknown>): EntityDetail['evidence'] {
  const items = Array.isArray(raw) ? raw : []
  const mapped = items.map((item) => {
    const body = record(item)
    return {
      provenance: body.rule === 'RKG.structure.contains.v1' || body.provenance === 'filesystem'
        ? 'filesystem' as const : 'source' as const,
      relative_path: safePath(body.file_path ?? body.relative_path),
      start_line: Number(body.start_line ?? body.line ?? 0),
      end_line: body.end_line == null ? undefined : Number(body.end_line),
    }
  }).filter((item) => item.relative_path)
  if (mapped.length > 0) return mapped
  const path = safePath(fallback?.file_path)
  if (!path) return []
  return [
    {
      relative_path: path,
      start_line: Number(fallback?.start_line ?? 0),
      end_line: fallback?.end_line == null ? undefined : Number(fallback.end_line),
    },
  ]
}

export function mapEntitySummary(raw: unknown): EntitySummary {
  const body = record(raw)
  const startLine = body.start_line == null ? undefined : Number(body.start_line)
  const endLine = body.end_line == null ? undefined : Number(body.end_line)
  const attributes = stringMap(body.attributes ?? {})
  return {
    ...(typeof attributes.method === "string" || typeof attributes.path === "string" ? {attributes: {method: typeof attributes.method === "string" ? attributes.method : undefined, path: typeof attributes.path === "string" ? attributes.path : undefined}} : {}),
    id: String(body.id ?? ''),
    type: uiEntityType(body.type),
    name: String(body.name ?? ''),
    qualified_name: String(body.qualified_name ?? ''),
    file_path: safePath(body.file_path),
    start_line:
      startLine != null && Number.isFinite(startLine) && startLine > 0
        ? startLine
        : undefined,
    end_line:
      endLine != null && Number.isFinite(endLine) && endLine > 0 ? endLine : undefined,
    scope_name: typeof attributes.module_name === 'string'
      ? attributes.module_name
      : typeof attributes.package_name === 'string'
        ? attributes.package_name : undefined,
    attributes: Object.keys(attributes).length ? attributes : undefined,
  }
}

export function mapEntityDetail(raw: unknown): EntityDetail {
  const body = record(raw)
  return {
    ...mapEntitySummary(body),
    snapshot_id: String(body.snapshot_id ?? ''),
    evidence: evidenceList(body.evidence, body),
    metadata: stringMap(body.attributes ?? body.metadata),
  }
}

function mapEdgeType(value: unknown): EdgeType {
  const text = String(value ?? '')
  if (EDGE_TYPES.has(text)) return text as EdgeType
  return 'depends_on'
}

export function mapGraphNode(raw: unknown): GraphNode {
  const body = record(raw)
  const attributes = stringMap(body.attributes ?? {})
  return {
    id: String(body.id ?? ''),
    type: uiEntityType(body.type),
    label: String(body.label ?? body.name ?? ''),
    qualified_name: String(body.qualified_name ?? ''),
    file_path: safePath(body.file_path),
    attributes: Object.keys(attributes).length ? attributes : undefined,
  }
}

export function mapGraphEdge(raw: unknown): GraphEdge {
  const body = record(raw)
  return {
    id: String(body.id ?? ''),
    source: String(body.source ?? body.source_id ?? ''),
    target: String(body.target ?? body.target_id ?? ''),
    type: mapEdgeType(body.type),
    label: String(body.label ?? body.type ?? body.rule ?? ''),
  }
}

export function mapSubgraph(raw: unknown): SubgraphResponse {
  const body = record(raw)
  const limits = record(body.limits)
  return {
    snapshot_id: String(body.snapshot_id ?? ''),
    root_id: String(body.root_id ?? ''),
    nodes: Array.isArray(body.nodes) ? body.nodes.map(mapGraphNode) : [],
    edges: Array.isArray(body.edges) ? body.edges.map(mapGraphEdge) : [],
    truncated: Boolean(body.truncated),
    truncation_reasons: Array.isArray(body.truncation_reasons)
      ? body.truncation_reasons.map(String)
      : [],
    limits: {
      depth: Number(limits.depth ?? 0),
      max_nodes: Number(limits.max_nodes ?? 0),
      max_edges: Number(limits.max_edges ?? 0),
    },
  }
}

export function mapTechnology(raw: unknown): TechnologyDetection {
  const body = record(raw)
  return {
    technology: String(body.technology ?? ''),
    version: (body.version as string | null | undefined) ?? null,
    support_state: supportState(body.support_state),
    evidence: evidenceList(body.evidence),
    limitations: Array.isArray(body.limitations) ? body.limitations.map(String) : [],
  }
}

function provenanceOf(body: Record<string, unknown>): DependencyItem['provenance'] {
  const values: string[] = []
  const push = (value: unknown) => {
    if (typeof value === 'string') values.push(value)
    else if (value && typeof value === 'object') {
      for (const nested of Object.values(value as Record<string, unknown>)) push(nested)
    }
  }
  push(body.subtype)
  push(body.kind)
  push(body.origin)
  push(body.provenance)
  for (const value of values) {
    const text = value.toLowerCase()
    if (text === 'usage' || text.endsWith('_usage')) return 'usage'
  }
  for (const value of values) {
    const text = value.toLowerCase()
    if (text === 'imported') return 'imported'
  }
  for (const value of values) {
    const text = value.toLowerCase()
    if (
      text === 'declared' ||
      text.startsWith('declared') ||
      text === 'lock' ||
      text === 'lock_only'
    ) {
      return 'declared'
    }
  }
  for (const value of values) {
    const text = value.toLowerCase()
    if (text.includes('usage')) return 'usage'
    if (text.includes('import')) return 'imported'
  }
  return 'declared'
}

export function mapDependency(raw: unknown): DependencyItem {
  const body = record(raw)
  const provenance = provenanceOf(body)
  return {
    id: String(body.id ?? ''),
    name: String(body.name ?? ''),
    version: (body.version as string | null | undefined) ?? null,
    subtype: provenance,
    provenance,
    evidence: evidenceList(body.evidence),
  }
}

export function mapDiagnostic(raw: unknown): DiagnosticItem {
  const body = record(raw)
  const severity = body.severity === 'error' || body.severity === 'info' ? body.severity : 'warning'
  return {
    id: String(body.id ?? ''),
    severity,
    code: String(body.code ?? ''),
    message: String(body.message ?? ''),
    evidence: evidenceList(body.evidence, body),
  }
}

const TURN_STATUS = new Set<ConversationTurnStatus>([
  'pending',
  'answered',
  'needs_clarification',
  'insufficient_evidence',
  'failed',
  'interrupted',
])

export function mapConversation(raw: unknown): ConversationSummary {
  const body = record(raw)
  const focus = body.focus_entity_id
  return {
    conversation_id: String(body.conversation_id ?? ''),
    repository_id: String(body.repository_id ?? ''),
    snapshot_id: String(body.snapshot_id ?? ''),
    title: String(body.title ?? ''),
    revision: Number(body.revision ?? 1),
    focus_entity_id: typeof focus === 'string' && focus ? focus : null,
    created_at: String(body.created_at ?? ''),
    updated_at: String(body.updated_at ?? ''),
  }
}

function mapClaims(value: unknown): Claim[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => {
    const body = record(item)
    return {
      text: String(body.text ?? ''),
      edge_id: body.edge_id == null ? undefined : String(body.edge_id),
      ...(Array.isArray(body.citation_indexes) && body.citation_indexes.every((i) => Number.isInteger(i) && i >= 0) ? {citation_indexes: body.citation_indexes as number[]} : {}),
    }
  })
}

function mapCitations(value: unknown): Citation[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => {
    const body = record(item)
    return {
      snapshot_id: String(body.snapshot_id ?? ''),
      ...(typeof body.edge_id === 'string' ? {edge_id: body.edge_id} : {}),
      entity_id: body.entity_id == null ? undefined : String(body.entity_id),
      evidence_id: body.evidence_id == null ? undefined : String(body.evidence_id),
      quote: body.quote == null ? undefined : String(body.quote),
    }
  })
}

function mapUsage(value: unknown): TurnUsage | null {
  const body = record(value)
  if (!Object.keys(body).length) return null
  return {
    input_tokens: body.input_tokens == null ? undefined : Number(body.input_tokens),
    output_tokens: body.output_tokens == null ? undefined : Number(body.output_tokens),
    model_calls: body.model_calls == null ? undefined : Number(body.model_calls),
  }
}

export function mapTurn(raw: unknown): ConversationTurn {
  const body = record(raw)
  const status = String(body.status ?? 'failed')
  return {
    turn_id: String(body.turn_id ?? ''),
    sequence: Number(body.sequence ?? 0),
    status: TURN_STATUS.has(status as ConversationTurnStatus)
      ? (status as ConversationTurnStatus)
      : 'failed',
    question: String(body.question ?? ''),
    resolved_question:
      body.resolved_question == null ? null : String(body.resolved_question),
    answer: body.answer == null ? null : String(body.answer),
    claims: mapClaims(body.claims),
    citations: mapCitations(body.citations),
    context_turn_ids: Array.isArray(body.context_turn_ids)
      ? body.context_turn_ids.map(String)
      : [],
    error_code: body.error_code == null ? null : String(body.error_code),
    ...(body.response_metadata !== undefined ? { response_metadata: readResponseMetadata(body.response_metadata) } : {}),
  }
}

export function mapConversationHistory(raw: unknown): ConversationHistory {
  const body = record(raw)
  const page = mapPage(raw, mapTurn)
  return {
    ...(typeof body.snapshot_available === 'boolean' ? {snapshot_available: body.snapshot_available} : {}),
    conversation: mapConversation(body.conversation),
    turns: page,
    candidate_entities: Array.isArray(body.candidate_entities)
      ? body.candidate_entities.map(mapEntitySummary)
      : [],
  }
}

export function mapTurnResult(raw: unknown): TurnSubmitResult {
  const body = record(raw)
  const limitations = Array.isArray(body.limitations) ? body.limitations.map(String) : []
  return {
    ...mapTurn(raw),
    schema_version: String(body.schema_version ?? ''),
    conversation_id: String(body.conversation_id ?? ''),
    revision: Number(body.revision ?? 0),
    repository_id: String(body.repository_id ?? ''),
    snapshot_id: String(body.snapshot_id ?? ''),
    candidate_entities: Array.isArray(body.candidate_entities)
      ? body.candidate_entities.map(mapEntitySummary)
      : [],
    limitations,
    retrieval_truncated: Boolean(body.retrieval_truncated),
    history_truncated: Boolean(body.history_truncated),
    usage: mapUsage(body.usage),
  }
}

export function mapContext(raw: unknown): ContextExport {
  const body = record(raw)
  const summary = body.diagnostic_summary
  const diagnostic_summary = Array.isArray(summary)
    ? summary.map(String)
    : Object.entries(record(summary)).map(([key, value]) => `${key}: ${String(value)}`)
  return {
    schema_version: String(body.schema_version ?? ''),
    repository_id: String(body.repository_id ?? ''),
    snapshot_id: String(body.snapshot_id ?? ''),
    root_id: String(body.root_id ?? ''),
    nodes: Array.isArray(body.nodes) ? body.nodes.map(mapGraphNode) : [],
    edges: Array.isArray(body.edges) ? body.edges.map(mapGraphEdge) : [],
    diagnostic_summary,
    truncated: Boolean(body.truncated),
    truncation_reasons: Array.isArray(body.truncation_reasons)
      ? body.truncation_reasons.map(String)
      : [],
  }
}
