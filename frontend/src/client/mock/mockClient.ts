import type {
  Citation,
  ContextExport,
  ContextRequest,
  ConversationCreateBody,
  ConversationHistory,
  ConversationCapabilities,
  ExactCitation,
  ConversationSummary,
  ConversationTurn,
  DependencyItem,
  DiagnosticItem,
  EdgeDirection,
  EdgeType,
  EntityDetail,
  EntitySummary,
  IndexJob,
  Paged,
  Repository,
  RepositoryCreateBody,
  RepositoryUpdateBody,
  Snapshot,
  SubgraphResponse,
  TechnologyDetection,
  TurnSubmitBody,
  TurnSubmitResult,
} from '../../types/api'
import { RkgApiError } from '../../types/api'
import {
  DEMO_REPO_ID,
  DEMO_SNAPSHOT_ID,
  seedConversationSnapshotRefs,
  seedDependencies,
  seedDiagnostics,
  seedEntities,
  seedEntityDetails,
  seedGraphEdges,
  seedGraphNodes,
  seedJobSucceeded,
  seedRepositories,
  seedSnapshots,
  seedTechnologies,
} from './fixtures'

export interface ListParams {
  q?: string
  offset?: number
  limit?: number
}

export interface SubgraphParams {
  snapshot_id: string
  root_id: string
  direction?: EdgeDirection
  edge_types?: EdgeType[]
  depth?: number
  max_nodes?: number
  max_edges?: number
  view?: 'flow' | 'neighborhood'
  include_structure?: boolean
  include_dependencies?: boolean
}

export interface RkgClient {
  listRepositories(params?: ListParams): Promise<Paged<Repository>>
  getRepository(id: string): Promise<Repository>
  createRepository(body: RepositoryCreateBody): Promise<Repository>
  updateRepository(id: string, body: RepositoryUpdateBody): Promise<Repository>
  deleteRepository(id: string): Promise<void>
  startIndexJob(
    repositoryId: string,
    body?: { app_candidate_id?: string },
  ): Promise<IndexJob>
  getIndexJob(jobId: string): Promise<{ job: IndexJob; retryAfter?: number }>
  listSnapshots(repositoryId: string, params?: ListParams): Promise<Paged<Snapshot>>
  getSnapshot(repositoryId: string, snapshotId: string): Promise<Snapshot>
  activateSnapshot(repositoryId: string, snapshotId: string): Promise<Repository>
  deleteSnapshot(repositoryId: string, snapshotId: string): Promise<void>
  searchEntities(
    snapshotId: string,
    params?: ListParams & { type?: string },
  ): Promise<Paged<EntitySummary>>
  getEntity(snapshotId: string, entityId: string): Promise<EntityDetail>
  getSubgraph(params: SubgraphParams): Promise<SubgraphResponse>
  listTechnologies(snapshotId: string): Promise<TechnologyDetection[]>
  listDependencies(
    snapshotId: string,
    params?: ListParams & { subtype?: string },
  ): Promise<Paged<DependencyItem>>
  listDiagnostics(
    snapshotId: string,
    params?: ListParams,
  ): Promise<Paged<DiagnosticItem>>
  exportContext(req: ContextRequest): Promise<ContextExport>
  listConversations(params?: ListParams & {
    repository_id?: string
    snapshot_id?: string
  }): Promise<Paged<ConversationSummary>>
  createConversation(body: ConversationCreateBody): Promise<ConversationSummary>
  getConversationCapabilities(): Promise<ConversationCapabilities>
  getExactCitation(conversationId: string, turnId: string, index: number): Promise<ExactCitation>
  getConversation(id: string, params?: ListParams & { include_unavailable?: boolean }): Promise<ConversationHistory>
  submitTurn(id: string, body: TurnSubmitBody): Promise<TurnSubmitResult>
  deleteConversation(id: string): Promise<void>
}

function pageOf<T>(items: T[], offset = 0, limit = 20): Paged<T> {
  const sliced = items.slice(offset, offset + limit)
  return {
    items: sliced,
    page: { offset, limit, total: items.length },
  }
}

function delay(ms = 180): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function nowIso(): string {
  return new Date().toISOString()
}

function redactPath(path: string): string {
  const cleaned = path.replace(/\\/g, '/').replace(/^\/+/, '')
  const parts = cleaned.split('/')
  if (parts.length <= 2) return `~/${cleaned}`
  return `~/…/${parts.slice(-2).join('/')}`
}

function assertSnapshot(snapshotId: string): void {
  const snap = seedSnapshots.find((s) => s.snapshot_id === snapshotId)
  if (!snap || snap.status === 'unavailable') {
    throw new RkgApiError(
      410,
      'snapshot_unavailable',
      'Snapshot không dùng được. Hãy lập chỉ mục lại từ trang chi tiết kho mã.',
    )
  }
}

function isTerminalStage(stage: IndexJob['stage']): boolean {
  return ['succeeded', 'succeeded_with_warnings', 'failed'].includes(stage)
}

/** In-memory mutable store for M0 mock UI. */
export function createMockClient(): RkgClient {
  const repositories = structuredClone(seedRepositories)
  const snapshots = structuredClone(seedSnapshots)
  const jobs = new Map<string, IndexJob>([[seedJobSucceeded.job_id, structuredClone(seedJobSucceeded)]])
  const conversationSnapshotRefs = new Set(seedConversationSnapshotRefs)
  const conversations: Array<ConversationSummary & { candidateIds: string[] }> = [
    {
      conversation_id: 'conv-orders-demo',
      repository_id: DEMO_REPO_ID,
      snapshot_id: DEMO_SNAPSHOT_ID,
      title: 'Order flow',
      revision: 2,
      focus_entity_id: 'ent-endpoint-get-order',
      created_at: '2026-09-24T09:00:00Z',
      updated_at: '2026-09-24T09:05:00Z',
      candidateIds: [],
    },
  ]
  const turnsById = new Map<string, ConversationTurn[]>([
    [
      'conv-orders-demo',
      [
        {
          turn_id: 'turn-orders-1',
          sequence: 1,
          status: 'answered',
          question: 'Which table does GET /orders/{id} read?',
          resolved_question: 'Which table does GET /orders/{id} read?',
          answer:
            'GET /orders/{id} reads the orders table. **bold** <script>alert(1)</script>',
          claims: [{ text: 'GET /orders/{id} reads the orders table.', edge_id: 'e5' }],
          citations: [
            {
              snapshot_id: DEMO_SNAPSHOT_ID,
              entity_id: 'ent-table-orders',
              evidence_id: 'ev-orders',
            },
          ],
          context_turn_ids: [],
          error_code: null,
        },
      ],
    ],
  ])
  const turnFingerprints = new Map<string, string>()
  const pendingIntents = new Map<string, {question: string; locale: "vi" | "en"}>()
  const rememberRefs = () => {
    conversationSnapshotRefs.clear()
    for (const id of seedConversationSnapshotRefs) conversationSnapshotRefs.add(id)
    for (const item of conversations) conversationSnapshotRefs.add(item.snapshot_id)
  }
  rememberRefs()
  let jobPollCount = new Map<string, number>()
  let seq = 10

  const nextId = (prefix: string) => {
    seq += 1
    return `${prefix}-${seq}`
  }

  const hasBusyJob = (repositoryId: string) =>
    [...jobs.values()].some(
      (j) => j.repository_id === repositoryId && !isTerminalStage(j.stage),
    )

  const hasConversationRefs = (repositoryId: string) =>
    snapshots.some(
      (s) =>
        s.repository_id === repositoryId && conversationSnapshotRefs.has(s.snapshot_id),
    )

  return {
    async listRepositories(params = {}) {
      await delay()
      const q = params.q?.trim().toLowerCase()
      let items = [...repositories].sort((a, b) => {
        const t = b.updated_at.localeCompare(a.updated_at)
        return t !== 0 ? t : a.repository_id.localeCompare(b.repository_id)
      })
      if (q) {
        items = items.filter((r) => r.display_name.toLowerCase().includes(q))
      }
      return pageOf(items, params.offset ?? 0, params.limit ?? 20)
    },

    async getRepository(id) {
      await delay()
      const repo = repositories.find((r) => r.repository_id === id)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      return structuredClone(repo)
    },

    async createRepository(body) {
      await delay(320)
      const path = body.path.trim()
      if (!path) {
        throw new RkgApiError(422, 'invalid_input', 'Đường dẫn là bắt buộc.')
      }
      if (path.includes('..') || path.toLowerCase().includes('outside')) {
        throw new RkgApiError(
          422,
          'invalid_input',
          'Đường dẫn nằm ngoài vùng cục bộ được phép. Hãy chọn đường dẫn trong vùng cho phép.',
        )
      }
      if (path.toLowerCase().includes('missing') || path.endsWith('/does-not-exist')) {
        throw new RkgApiError(
          422,
          'invalid_input',
          'Đường dẫn không tồn tại trên máy chủ RKG. Việc đăng ký không sửa hệ thống tệp của bạn.',
        )
      }
      if (!body.display_name.trim()) {
        throw new RkgApiError(422, 'invalid_input', 'Tên hiển thị là bắt buộc.')
      }

      const duplicate = repositories.find(
        (r) => r.source_locator_redacted === redactPath(path),
      )
      if (duplicate) {
        throw new RkgApiError(
          409,
          'repository_conflict',
          'Đã có kho mã với cùng định danh nguồn này.',
        )
      }

      const repo: Repository = {
        repository_id: nextId('repo'),
        revision: 1,
        display_name: body.display_name.trim(),
        source_type: 'local',
        source_locator_redacted: redactPath(path),
        source_root: body.source_root ?? '.',
        app_module: body.app_module ?? null,
        app_symbol: body.app_symbol ?? null,
        scan_defaults: body.scan_defaults ?? null,
        active_snapshot_id: null,
        created_at: nowIso(),
        updated_at: nowIso(),
      }
      repositories.unshift(repo)
      return structuredClone(repo)
    },

    async updateRepository(id, body) {
      await delay(240)
      const repo = repositories.find((r) => r.repository_id === id)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')

      if (body.expected_revision !== repo.revision) {
        throw new RkgApiError(
          409,
          'repository_conflict',
          'Kho mã đã được cập nhật ở nơi khác. Hãy tải lại, xem lại bản nháp, rồi thử lại.',
        )
      }

      if (body.display_name !== undefined) {
        const name = body.display_name.trim()
        if (!name) {
          throw new RkgApiError(422, 'invalid_input', 'Tên hiển thị là bắt buộc.')
        }
        repo.display_name = name
      }
      if (body.source_root !== undefined) repo.source_root = body.source_root
      if (body.app_module !== undefined) repo.app_module = body.app_module
      if (body.app_symbol !== undefined) repo.app_symbol = body.app_symbol
      if (body.scan_defaults !== undefined) repo.scan_defaults = body.scan_defaults

      repo.revision += 1
      repo.updated_at = nowIso()
      return structuredClone(repo)
    },

    async deleteRepository(id) {
      await delay(260)
      const idx = repositories.findIndex((r) => r.repository_id === id)
      if (idx < 0) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')

      if (hasBusyJob(id)) {
        throw new RkgApiError(
          409,
          'repository_busy',
          'Một job lập chỉ mục vẫn đang chạy. Hãy đợi job hoàn tất rồi mới xóa.',
        )
      }
      if (hasConversationRefs(id)) {
        throw new RkgApiError(
          409,
          'repository_in_use',
          'Một cuộc hội thoại vẫn tham chiếu snapshot trong kho mã này. Hãy gỡ các tham chiếu đó trước.',
        )
      }

      for (let i = snapshots.length - 1; i >= 0; i -= 1) {
        if (snapshots[i]?.repository_id === id) {
          conversationSnapshotRefs.delete(snapshots[i]!.snapshot_id)
          snapshots.splice(i, 1)
        }
      }
      for (const [jobId, job] of [...jobs.entries()]) {
        if (job.repository_id === id) jobs.delete(jobId)
      }
      repositories.splice(idx, 1)
    },

    async startIndexJob(repositoryId, body = {}) {
      await delay(220)
      const repo = repositories.find((r) => r.repository_id === repositoryId)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')

      if (hasBusyJob(repositoryId)) {
        throw new RkgApiError(
          409,
          'index_job_busy',
          'Đã có job lập chỉ mục đang chạy cho kho mã này.',
        )
      }

      const jobId = nextId('job')
      const needsSelection = repositoryId !== DEMO_REPO_ID && !body.app_candidate_id && !repo.app_module

      const job: IndexJob = {
        job_id: jobId,
        repository_id: repositoryId,
        stage: 'queued',
        progress_revision: 1,
        message: 'Job đã vào hàng đợi',
        report: needsSelection
          ? {
              summary: 'Phát hiện nhiều điểm vào ứng dụng.',
              warnings: [],
              app_candidates: [
                {
                  candidate_id: 'app-a',
                  module: 'app.main',
                  symbol: 'app',
                  evidence: 'app/main.py:10',
                },
                {
                  candidate_id: 'app-b',
                  module: 'app.api',
                  symbol: 'api',
                  evidence: 'app/api/__init__.py:4',
                },
              ],
              selected_app_id: null,
              technologies: [
                { technology: 'fastapi', support_state: 'supported_patterns' },
                { technology: 'sqlalchemy', support_state: 'supported_patterns' },
              ],
            }
          : {
              summary: 'Đang phát hiện công nghệ…',
              warnings: [],
              selected_app_id: body.app_candidate_id ?? 'app-main',
              technologies: [
                { technology: 'fastapi', support_state: 'supported_patterns' },
              ],
            },
        snapshot_id: null,
        error: null,
        updated_at: nowIso(),
        retry_after_seconds: 1,
      }

      // Block at detecting until app is chosen when multiple candidates
      if (needsSelection) {
        job.stage = 'detecting'
        job.message = 'Chọn điểm vào ứng dụng để tiếp tục'
      }

      jobs.set(jobId, job)
      jobPollCount.set(jobId, 0)
      return structuredClone(job)
    },

    async getIndexJob(jobId) {
      await delay(120)
      const job = jobs.get(jobId)
      if (!job) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')

      const polls = (jobPollCount.get(jobId) ?? 0) + 1
      jobPollCount.set(jobId, polls)

      const terminal = isTerminalStage(job.stage)
      if (!terminal) {
        const waitingForApp =
          job.stage === 'detecting' &&
          (job.report?.app_candidates?.length ?? 0) > 1 &&
          !job.report?.selected_app_id

        if (!waitingForApp) {
          if (job.stage === 'queued' && polls >= 1) {
            job.stage = 'detecting'
            job.message = 'Đang phát hiện ứng dụng và adapter'
            job.progress_revision += 1
          } else if (job.stage === 'detecting' && polls >= 2) {
            job.stage = 'indexing'
            job.message = 'Đang lập chỉ mục mã nguồn và dựng đồ thị'
            job.progress_revision += 1
          } else if (job.stage === 'indexing' && polls >= 4) {
            const snapId = nextId('snap')
            const snap: Snapshot = {
              snapshot_id: snapId,
              repository_id: job.repository_id,
              source_revision: `manifest:${snapId.replace(/\W/g, '')}${'0'.repeat(40)}`.slice(0, 73),
              manifest_hash: `sha256:${snapId}${'ab'.repeat(20)}`.slice(0, 71),
              scan_config_digest: `sha256:cfg${snapId}`,
              analyzer_version: '0.1.0-m0',
              schema_version: 'graph-1',
              adapter_versions: { fastapi: '0.1.0' },
              status: 'ready',
              metrics: { entity_count: 12, edge_count: 14, warning_count: 0 },
              capabilities: { technologies: ['fastapi'], graph_ready: true },
              created_at: nowIso(),
              is_active: true,
            }
            for (const s of snapshots) {
              if (s.repository_id === job.repository_id) s.is_active = false
            }
            snapshots.unshift(snap)
            const repo = repositories.find((r) => r.repository_id === job.repository_id)
            if (repo) {
              repo.active_snapshot_id = snapId
              repo.updated_at = nowIso()
              repo.revision += 1
            }
            job.stage = 'succeeded'
            job.message = 'Lập chỉ mục thành công'
            job.snapshot_id = snapId
            job.progress_revision += 1
            job.report = {
              summary: 'Lập chỉ mục thành công (mock).',
              warnings: [],
              selected_app_id: job.report?.selected_app_id ?? 'app-main',
              technologies: job.report?.technologies ?? [],
            }
          }
          job.updated_at = nowIso()
        }
      }

      const retryAfter = terminal ? undefined : (job.retry_after_seconds ?? 1)
      return { job: structuredClone(job), retryAfter }
    },

    async listSnapshots(repositoryId, params = {}) {
      await delay()
      const repo = repositories.find((r) => r.repository_id === repositoryId)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      const items = snapshots
        .filter((s) => s.repository_id === repositoryId)
        .sort((a, b) => {
          const t = b.created_at.localeCompare(a.created_at)
          return t !== 0 ? t : a.snapshot_id.localeCompare(b.snapshot_id)
        })
      return pageOf(items, params.offset ?? 0, params.limit ?? 20)
    },

    async getSnapshot(repositoryId, snapshotId) {
      await delay()
      const snap = snapshots.find(
        (s) => s.repository_id === repositoryId && s.snapshot_id === snapshotId,
      )
      if (!snap) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      return structuredClone(snap)
    },

    async activateSnapshot(repositoryId, snapshotId) {
      await delay(200)
      const repo = repositories.find((r) => r.repository_id === repositoryId)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      const snap = snapshots.find(
        (s) => s.repository_id === repositoryId && s.snapshot_id === snapshotId,
      )
      if (!snap) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      if (snap.status === 'unavailable') {
        throw new RkgApiError(410, 'snapshot_unavailable', 'Snapshot không dùng được.')
      }
      for (const s of snapshots) {
        if (s.repository_id === repositoryId) s.is_active = s.snapshot_id === snapshotId
      }
      repo.active_snapshot_id = snapshotId
      repo.updated_at = nowIso()
      repo.revision += 1
      return structuredClone(repo)
    },

    async deleteSnapshot(repositoryId, snapshotId) {
      await delay(240)
      const repo = repositories.find((r) => r.repository_id === repositoryId)
      if (!repo) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      const idx = snapshots.findIndex(
        (s) => s.repository_id === repositoryId && s.snapshot_id === snapshotId,
      )
      if (idx < 0) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')

      const snap = snapshots[idx]!
      if (snap.is_active || repo.active_snapshot_id === snapshotId) {
        throw new RkgApiError(
          409,
          'snapshot_active',
          'Hãy kích hoạt snapshot khác trước khi xóa snapshot đang dùng.',
        )
      }
      if (conversationSnapshotRefs.has(snapshotId)) {
        throw new RkgApiError(
          409,
          'snapshot_in_use',
          'Một cuộc hội thoại vẫn tham chiếu snapshot này. Hãy gỡ các tham chiếu đó trước.',
        )
      }

      snapshots.splice(idx, 1)
    },

    async searchEntities(snapshotId, params = {}) {
      await delay()
      assertSnapshot(snapshotId)
      // New repos that just indexed reuse demo graph for UI smoke
      const q = params.q?.trim().toLowerCase()
      let items = [...seedEntities]
      if (params.type) items = items.filter((e) => e.type === params.type)
      if (q) {
        items = items.filter(
          (e) =>
            e.name.toLowerCase().includes(q) ||
            e.qualified_name.toLowerCase().includes(q),
        )
      }
      items.sort((a, b) => {
        const t = a.type.localeCompare(b.type)
        if (t !== 0) return t
        const n = a.qualified_name.localeCompare(b.qualified_name)
        return n !== 0 ? n : a.id.localeCompare(b.id)
      })
      return pageOf(items, params.offset ?? 0, params.limit ?? 20)
    },

    async getEntity(snapshotId, entityId) {
      await delay()
      assertSnapshot(snapshotId)
      const detail = seedEntityDetails[entityId]
      if (!detail) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy.')
      return { ...structuredClone(detail), snapshot_id: snapshotId }
    },

    async getSubgraph(params) {
      await delay(220)
      assertSnapshot(params.snapshot_id)
      const direction = params.direction ?? 'both'
      const depth = Math.min(params.depth ?? 1, 6)
      const maxNodes = Math.min(params.max_nodes ?? 50, 200)
      const maxEdges = Math.min(params.max_edges ?? 400, 400)
      const edgeFilter = params.edge_types

      const root = seedGraphNodes.find((n) => n.id === params.root_id)
      if (!root) throw new RkgApiError(404, 'generic_not_found', 'Không tìm thấy thực thể gốc.')

      const allowed = new Set(
        (edgeFilter ? seedGraphEdges.filter((e) => edgeFilter.includes(e.type)) : seedGraphEdges).map(
          (e) => e.id,
        ),
      )
      const flow = params.view === 'flow' && !['file', 'module', 'directory'].includes(root.type)
      const upstream = ['table', 'topic', 'config', 'dependency'].includes(root.type)
      const traversalDirection = flow ? (upstream ? 'incoming' : 'outgoing') : direction
      const flowAllows = (id: string, edge: (typeof seedGraphEdges)[0]) => {
        if (!flow) return true
        const node = seedGraphNodes.find((n) => n.id === id)
        if (id !== root.id && node?.type !== 'function') return false
        const kinds = new Set<EdgeType>(['handled_by', 'calls'])
        if (!upstream || id === root.id) {
          for (const kind of ['reads', 'writes', 'publishes', 'consumes'] as EdgeType[]) kinds.add(kind)
        }
        if (params.include_dependencies || (upstream && id === root.id)) kinds.add('depends_on')
        if (id === root.id && ['class', 'interface'].includes(root.type)) {
          kinds.add('contains'); kinds.add('maps_to')
        }
        return kinds.has(edge.type)
      }

      const nodes = new Map<string, (typeof seedGraphNodes)[0]>()
      const edges: typeof seedGraphEdges = []
      nodes.set(root.id, root)

      let frontier = [root.id]
      for (let d = 0; d < depth && nodes.size < maxNodes; d += 1) {
        const next: string[] = []
        for (const id of frontier) {
          for (const edge of seedGraphEdges) {
            if (!allowed.has(edge.id)) continue
            if (!flowAllows(id, edge)) continue
            let other: string | null = null
            if (
              (traversalDirection === 'outgoing' || traversalDirection === 'both') &&
              edge.source === id
            ) {
              other = edge.target
            } else if (
              (traversalDirection === 'incoming' || traversalDirection === 'both') &&
              edge.target === id
            ) {
              other = edge.source
            }
            if (!other) continue
            if (edges.length >= maxEdges) break
            if (!edges.find((e) => e.id === edge.id)) edges.push(edge)
            if (!nodes.has(other)) {
              const node = seedGraphNodes.find((n) => n.id === other)
              if (node) {
                nodes.set(other, node)
                next.push(other)
              }
            }
            if (nodes.size >= maxNodes) break
          }
        }
        frontier = next
      }

      if (flow && params.include_structure) {
        const pending = [...nodes.keys()]
        const seen = new Set<string>()
        while (pending.length) {
          const child = pending.shift()!
          if (seen.has(child)) continue
          seen.add(child)
          for (const edge of seedGraphEdges) {
            if (edge.type !== 'contains' || edge.target !== child) continue
            const parent = seedGraphNodes.find((n) => n.id === edge.source)
            if (!parent || edges.some((e) => e.id === edge.id)) continue
            if (edges.length >= maxEdges || (!nodes.has(parent.id) && nodes.size >= maxNodes)) continue
            nodes.set(parent.id, parent)
            edges.push(edge)
            pending.push(parent.id)
          }
        }
      }

      const truncated = nodes.size >= maxNodes || edges.length >= maxEdges
      return {
        snapshot_id: params.snapshot_id,
        root_id: params.root_id,
        nodes: [...nodes.values()],
        edges,
        truncated,
        truncation_reasons: truncated ? ['budget_reached'] : [],
        limits: { depth, max_nodes: maxNodes, max_edges: maxEdges },
      }
    },

    async listTechnologies(snapshotId) {
      await delay()
      assertSnapshot(snapshotId)
      return structuredClone(seedTechnologies)
    },

    async listDependencies(snapshotId, params = {}) {
      await delay()
      assertSnapshot(snapshotId)
      let items = [...seedDependencies]
      if (params.subtype) items = items.filter((d) => d.subtype === params.subtype)
      if (params.q) {
        const q = params.q.toLowerCase()
        items = items.filter((d) => d.name.toLowerCase().includes(q))
      }
      return pageOf(items, params.offset ?? 0, params.limit ?? 20)
    },

    async listDiagnostics(snapshotId, params = {}) {
      await delay()
      assertSnapshot(snapshotId)
      return pageOf(seedDiagnostics, params.offset ?? 0, params.limit ?? 20)
    },

    async exportContext(req) {
      await delay(400)
      assertSnapshot(req.snapshot_id)
      const graph = await this.getSubgraph({
        snapshot_id: req.snapshot_id,
        root_id: req.root_id,
        direction: req.direction,
        edge_types: req.edge_types,
        depth: req.depth,
        max_nodes: req.max_nodes,
        max_edges: req.max_edges,
        view: req.view,
        include_structure: req.include_structure,
        include_dependencies: req.include_dependencies,
      })
      const repo =
        repositories.find((r) => r.active_snapshot_id === req.snapshot_id) ??
        repositories.find((r) => r.repository_id === DEMO_REPO_ID)
      return {
        schema_version: 'context-1',
        repository_id: repo?.repository_id ?? DEMO_REPO_ID,
        snapshot_id: req.snapshot_id,
        root_id: req.root_id,
        nodes: graph.nodes,
        edges: graph.edges,
        diagnostic_summary: seedDiagnostics.map((d) => d.message),
        truncated: graph.truncated || req.max_chars < 5000,
        truncation_reasons: [
          ...(graph.truncation_reasons ?? []),
          ...(req.max_chars < 5000 ? ['max_chars'] : []),
        ],
      }
    },

    async listConversations(params = {}) {
      await delay()
      let items = [...conversations]
      if (params.repository_id) {
        items = items.filter((item) => item.repository_id === params.repository_id)
      }
      if (params.snapshot_id) {
        items = items.filter((item) => item.snapshot_id === params.snapshot_id)
      }
      items.sort((a, b) => {
        const byTime = b.updated_at.localeCompare(a.updated_at)
        return byTime !== 0 ? byTime : a.conversation_id.localeCompare(b.conversation_id)
      })
      const page = pageOf(items, params.offset ?? 0, params.limit ?? 20)
      return {
        items: page.items.map(({ candidateIds: _ignored, ...item }) => item),
        page: page.page,
      }
    },

    async createConversation(body) {
      await delay()
      const repo = repositories.find((item) => item.repository_id === body.repository_id)
      if (!repo) throw new RkgApiError(404, 'not_found', 'Không tìm thấy.')
      const snapshotId = body.snapshot_id || repo.active_snapshot_id
      if (!snapshotId) {
        throw new RkgApiError(409, 'no_active_snapshot', 'Kho mã chưa có snapshot đang dùng.')
      }
      const snap = snapshots.find(
        (item) => item.repository_id === repo.repository_id && item.snapshot_id === snapshotId,
      )
      if (!snap) throw new RkgApiError(404, 'not_found', 'Không tìm thấy.')
      if (snap.status === 'unavailable') {
        throw new RkgApiError(410, 'snapshot_unavailable', 'Snapshot không dùng được.')
      }
      const created: ConversationSummary & { candidateIds: string[] } = {
        conversation_id: nextId('conv'),
        repository_id: repo.repository_id,
        snapshot_id: snapshotId,
        title: body.title?.trim() ?? '',
        revision: 1,
        focus_entity_id: null,
        created_at: nowIso(),
        updated_at: nowIso(),
        candidateIds: [],
      }
      conversations.push(created)
      turnsById.set(created.conversation_id, [])
      rememberRefs()
      const { candidateIds: _ignored, ...summary } = created
      return summary
    },

    async getConversationCapabilities() {
      return { schema_version: 'rkg.conversation-capabilities/1', features: ['ui_locale','response_metadata_v1','exact_citation_lookup','history_unavailable'], provider_enabled: true }
    },

    async getExactCitation(id, turnId, index) {
      await delay()
      const conversation = conversations.find((item) => item.conversation_id === id)
      const turn = turnsById.get(id)?.find((item) => item.turn_id === turnId)
      const citation = turn?.citations[index]
      if (!conversation || !turn || !citation?.evidence_id || citation.snapshot_id !== conversation.snapshot_id || citation.evidence_id !== 'ev-orders') throw new RkgApiError(404, 'not_found', 'Citation unavailable.')
      const snapshot = snapshots.find((item) => item.snapshot_id === conversation.snapshot_id)
      if (!snapshot || snapshot.status !== 'ready') throw new RkgApiError(410, 'snapshot_unavailable', 'Snapshot unavailable.')
      return { schema_version: 'rkg.citation/1', conversation_id: id, turn_id: turnId, citation_index: index, snapshot_id: conversation.snapshot_id,
        evidence: { id: 'ev-orders', file_path: 'app/models.py', provenance: 'source', start_line: 43, end_line: 45, rule: 'synthetic.reads' } }
    },

    async getConversation(id, params = {}) {
      await delay()
      const conversation = conversations.find((item) => item.conversation_id === id)
      if (!conversation) throw new RkgApiError(404, 'not_found', 'Không tìm thấy.')
      const snap = snapshots.find((item) => item.snapshot_id === conversation.snapshot_id)
      if ((!snap || snap.status === 'unavailable') && !params.include_unavailable) {
        throw new RkgApiError(410, 'snapshot_unavailable', 'Snapshot không dùng được.')
      }
      const all = turnsById.get(id) ?? []
      const page = pageOf(all, params.offset ?? 0, params.limit ?? 100)
      const { candidateIds, ...summary } = conversation
      return {
        conversation: summary,
        turns: page,
        snapshot_available: snap?.status === "ready",
        candidate_entities: (snap?.status === "ready" ? candidateIds : [])
          .map((entityId) => seedEntities.find((item) => item.id === entityId))
          .filter((item): item is EntitySummary => Boolean(item))
          .map((item) => structuredClone(item)),
      }
    },

    async submitTurn(id, body) {
      await delay()
      const conversation = conversations.find((item) => item.conversation_id === id)
      if (!conversation) throw new RkgApiError(404, 'not_found', 'Không tìm thấy.')
      const snap = snapshots.find((item) => item.snapshot_id === conversation.snapshot_id)
      if (!snap || snap.status === 'unavailable') {
        throw new RkgApiError(410, 'snapshot_unavailable', 'Snapshot không dùng được.')
      }
      if (!body.question?.trim() || !body.client_request_id?.trim()) {
        throw new RkgApiError(422, 'invalid_turn_request', 'Câu hỏi hoặc mã phiên bản không hợp lệ.')
      }
      if (!Number.isInteger(body.expected_revision) || body.expected_revision < 1) {
        throw new RkgApiError(422, 'invalid_turn_request', 'Câu hỏi hoặc mã phiên bản không hợp lệ.')
      }
      const key = `${id}:${body.client_request_id}`
      if (body.ui_locale != null && !['vi','en'].includes(body.ui_locale)) throw new RkgApiError(422, 'invalid_turn_request', 'Invalid locale.')
      const fingerprint = JSON.stringify({ question: body.question, root_id: body.root_id ?? null, ...(body.ui_locale === 'en' ? {ui_locale: 'en'} : {}) })
      const previous = turnFingerprints.get(key)
      const history = turnsById.get(id) ?? []
      if (previous) {
        if (previous !== fingerprint) {
          throw new RkgApiError(409, 'conversation_conflict', 'Hội thoại đã đổi.')
        }
        const replay = history.find((item) => item.turn_id === `turn-${key}`)
        if (replay && replay.status !== 'failed' && replay.status !== 'pending') {
          return mockTurnResult(conversation, replay)
        }
      }
      if (history.some((item) => item.status === 'pending')) {
        throw new RkgApiError(409, 'conversation_busy', 'Hội thoại đang bận.')
      }
      if (body.expected_revision !== conversation.revision) {
        throw new RkgApiError(409, 'conversation_conflict', 'Hội thoại đã đổi.')
      }
      const sequence = history.length + 1
      const lowered = body.question.toLowerCase()
      let status: ConversationTurn['status'] = 'answered'
      let answer: string | null = 'GET /orders/{id} reads the orders table.'
      let claims: ConversationTurn['claims'] = [
        { text: 'GET /orders/{id} reads the orders table.', edge_id: 'e5' },
      ]
      let citations: Citation[] = [
        { snapshot_id: conversation.snapshot_id, entity_id: 'ent-table-orders', evidence_id: 'ev-orders', edge_id: 'e5' },
      ]
      let errorCode: string | null = null
      let resolvedQuestion = body.question
      let effectiveLocale = body.ui_locale ?? 'vi'
      const isGreeting = /^(hello|hi|hey|alo|xin chào|xin chao|chào|chao)[!.?]*$/i.test(body.question.trim())
      const ordinal = body.question.trim().match(/^(?:candidate\s+)?(-?\d+)$/)
      if (isGreeting) {
        claims = []; citations = []
      } else if (body.root_id || (ordinal && conversation.candidateIds.length)) {
        const selected = body.root_id ?? conversation.candidateIds[Number(ordinal?.[1] ?? 1) - 1]
        const pending = pendingIntents.get(id)
        const entity = seedEntities.find((item) => item.id === selected)
        if (!entity || (conversation.candidateIds.includes(selected ?? '') && !pending)) {
          status = 'needs_clarification'; claims = []; citations = []
          answer = 'Choose an available candidate or restate the original question.'
        } else {
          if (conversation.candidateIds.includes(entity.id) && pending) {
            resolvedQuestion = pending.question; effectiveLocale = pending.locale
          }
          conversation.focus_entity_id = entity.id
          conversation.candidateIds = []
          answer = entity.qualified_name + ' reads the orders table.'
          claims = [{text: answer, edge_id: 'e5'}]
        }
      } else if (lowered.includes('which') || lowered.includes('ambiguous')) {
        status = 'needs_clarification'
        answer = 'Please choose one candidate by number.'
        claims = []
        citations = []
        conversation.candidateIds = ['ent-endpoint-get-order', 'ent-fn-get-order']
      } else if (lowered.includes('timeout')) {
        status = 'failed'
        answer = null
        claims = []
        citations = []
        errorCode = 'llm_timeout'
      } else if (lowered.includes('provider disabled')) {
        status = 'failed'
        answer = null
        claims = []
        citations = []
        errorCode = 'llm_disabled'
      } else if (lowered.includes('not in the graph') || lowered.includes('unknown topic')) {
        status = 'insufficient_evidence'
        answer = 'Insufficient evidence in this snapshot.'
        claims = []
        citations = []
      } else if (lowered.includes(' it ') || lowered.startsWith('it ') || lowered.includes(' it?')) {
        answer = 'The focused endpoint still reads the orders table.'
        claims = [{ text: answer, edge_id: 'e5' }]
      }
      const language = /\b(hello|hi|hey|what|which|does|reads|calls)\b/i.test(resolvedQuestion) ? 'en' : /[ăâđêôơư\u1ea0-\u1ef9]|\b(alo|goi|ham|nhung|dang|chao)\b/i.test(resolvedQuestion) ? 'vi' : effectiveLocale
      if (isGreeting) { status = 'answered'; answer = language === 'vi' ? 'Xin chào! Bạn có thể hỏi về endpoint hoặc hàm.' : 'Hello! Ask about an endpoint or function.'; claims = []; citations = [] }
      if (status === 'needs_clarification' && !ordinal && !body.root_id) pendingIntents.set(id, {question: body.question.trim(), locale: body.ui_locale ?? 'vi'})
      if (status === 'answered' && !isGreeting) { pendingIntents.delete(id); conversation.candidateIds = [] }
      claims = claims.map((claim, index) => ({...claim, citation_indexes: [index]}))
      const limits = [...(lowered.includes('older turns') ? ['history_truncated'] : []), ...(lowered.includes('truncated') ? ['max_nodes'] : [])]
      const subjectEntity = seedEntities.find((entity) => entity.id === (conversation.focus_entity_id ?? 'ent-endpoint-get-order'))
      const subjectTypes: Record<string, string> = { endpoint: 'Endpoint', function: 'Callable', class: 'Type', interface: 'Type', table: 'DataResource', topic: 'MessageChannel', config: 'Configuration', dependency: 'ExternalDependency', directory: 'Directory', file: 'SourceUnit', module: 'Namespace' }
      const turn: ConversationTurn = {
        turn_id: `turn-${key}`,
        sequence,
        status,
        question: body.question,
        resolved_question: status === 'failed' ? null : resolvedQuestion,
        answer,
        claims,
        citations,
        context_turn_ids: history
          .filter((item) => item.status === 'answered')
          .slice(-6)
          .map((item) => item.turn_id),
        error_code: errorCode,
        response_metadata: { version: 1, language, kind: isGreeting ? 'greeting' : status === 'answered' ? 'answer' : status === 'needs_clarification' ? 'clarification' : status === 'insufficient_evidence' ? 'insufficient' : 'error',
          subject: status === 'answered' && !isGreeting ? {entity_id: subjectEntity?.id ?? 'ent-endpoint-get-order', type: subjectTypes[subjectEntity?.type ?? 'endpoint'], name: subjectEntity?.name ?? 'get_order', qualified_name: subjectEntity?.qualified_name ?? 'app.api.orders:get_order', method: subjectEntity?.type === 'endpoint' ? 'GET' : null, path: subjectEntity?.type === 'endpoint' ? '/orders/{id}' : null} : null,
          coverage: isGreeting || status === 'needs_clarification' ? 'not_applicable' : limits.length ? 'partial' : status === 'failed' ? 'unknown' : 'complete',
          retrieval_truncated: lowered.includes('truncated'), history_truncated: lowered.includes('older turns'), limitations: limits,
          insufficient_reason: status === 'insufficient_evidence' ? 'entity_not_found' : null },
      }
      history.push(turn)
      turnsById.set(id, history)
      conversation.revision += 1
      conversation.updated_at = nowIso()
      turnFingerprints.set(key, fingerprint)
      if (status === 'failed' && errorCode === 'llm_timeout') {
        throw new RkgApiError(504, 'llm_timeout', 'Nhà cung cấp mô hình quá thời gian.')
      }
      if (status === 'failed' && errorCode === 'llm_disabled') {
        throw new RkgApiError(503, 'llm_disabled', 'Nhà cung cấp mô hình chưa được cấu hình.')
      }
      if (status === 'failed') {
        throw new RkgApiError(502, errorCode ?? 'llm_provider_error', 'Nhà cung cấp mô hình trả lỗi.')
      }
      return {
        ...mockTurnResult(conversation, turn),
        history_truncated: lowered.includes('older turns'),
        retrieval_truncated: lowered.includes('truncated'),
        limitations: [
          ...(lowered.includes('older turns') ? ['history_truncated'] : []),
          ...(lowered.includes('truncated') ? ['max_nodes'] : []),
        ],
      }
    },

    async deleteConversation(id) {
      await delay()
      const index = conversations.findIndex((item) => item.conversation_id === id)
      if (index < 0) throw new RkgApiError(404, 'not_found', 'Không tìm thấy.')
      const history = turnsById.get(id) ?? []
      if (history.some((item) => item.status === 'pending')) {
        throw new RkgApiError(409, 'conversation_busy', 'Hội thoại đang bận.')
      }
      conversations.splice(index, 1)
      turnsById.delete(id)
      rememberRefs()
    },
  }
}

function mockTurnResult(
  conversation: ConversationSummary & { candidateIds: string[] },
  turn: ConversationTurn,
): TurnSubmitResult {
  return {
    ...turn,
    schema_version: 'rkg.conversation/1',
    conversation_id: conversation.conversation_id,
    revision: conversation.revision,
    repository_id: conversation.repository_id,
    snapshot_id: conversation.snapshot_id,
    candidate_entities: conversation.candidateIds
      .map((entityId) => seedEntities.find((item) => item.id === entityId))
      .filter((item): item is EntitySummary => Boolean(item))
      .map((item) => structuredClone(item)),
    limitations: turn.response_metadata?.limitations ?? [],
    retrieval_truncated: turn.response_metadata?.retrieval_truncated === true,
    history_truncated: turn.response_metadata?.history_truncated === true,
    usage: { model_calls: turn.response_metadata?.kind === 'greeting' ? 0 : turn.status === 'answered' ? 1 : 0 },
  }
}

/** Resume a detecting job after explicit app selection (mock helper used by UI). */
export async function selectAppAndContinue(
  client: RkgClient,
  repositoryId: string,
  appCandidateId: string,
): Promise<IndexJob> {
  return client.startIndexJob(repositoryId, { app_candidate_id: appCandidateId })
}

export { DEMO_REPO_ID, DEMO_SNAPSHOT_ID }
