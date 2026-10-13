import type { RkgClient, ListParams, SubgraphParams } from '../mock/mockClient'
import { RkgApiError } from '../../types/api'
import type {
  ContextRequest,
  ConversationCreateBody,
  RepositoryCreateBody,
  RepositoryUpdateBody,
  TurnSubmitBody,
  ConversationCapabilities,
  ExactCitation,
} from '../../types/api'
import {
  domainEntityType,
  mapContext,
  mapConversation,
  mapConversationHistory,
  mapDependency,
  mapDiagnostic,
  mapEntityDetail,
  mapEntitySummary,
  mapJob,
  mapPage,
  mapRepository,
  mapSnapshot,
  mapSubgraph,
  mapTechnology,
  mapTurnResult,
  safeMessage,
} from './mapWire'

export interface LiveClientOptions {
  baseUrl?: string
  sessionToken?: string
  fetchImpl?: typeof fetch
}

function trimBase(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '')
}

function queryString(params: Record<string, string | number | string[] | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, item)
    } else {
      search.set(key, String(value))
    }
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export function createLiveClient(options: LiveClientOptions = {}): RkgClient {
  const baseUrl = trimBase(options.baseUrl ?? '')
  const sessionToken = options.sessionToken ?? ''
  const fetchImpl = options.fetchImpl ?? fetch

  async function request(
    method: string,
    path: string,
    init?: { query?: Record<string, string | number | string[] | undefined>; body?: unknown },
  ): Promise<{ data: unknown; retryAfter: string | null }> {
    const headers = new Headers()
    if (sessionToken) headers.set('X-RKG-Session', sessionToken)
    if (init?.body !== undefined) headers.set('Content-Type', 'application/json')
    let response: Response
    try {
      response = await fetchImpl(`${baseUrl}/api/v1${path}${queryString(init?.query ?? {})}`, {
        method,
        headers,
        body: init?.body === undefined ? undefined : JSON.stringify(init.body),
      })
    } catch {
      throw new RkgApiError(0, 'unavailable', 'Không kết nối được máy chủ RKG trên vòng lặp cục bộ.')
    }
    if (response.status === 204) return { data: null, retryAfter: response.headers.get('Retry-After') }
    const text = await response.text()
    let payload: unknown = null
    if (text) {
      try {
        payload = JSON.parse(text) as unknown
      } catch {
        throw new RkgApiError(response.status, 'invalid_request', 'Máy chủ trả dữ liệu không đọc được.')
      }
    }
    if (!response.ok) {
      const error = payload && typeof payload === 'object' && 'error' in payload
        ? (payload as { error?: { code?: string; message?: string } }).error
        : undefined
      const code = error?.code || 'invalid_request'
      throw new RkgApiError(response.status, code, safeMessage(code, error?.message))
    }
    return { data: payload, retryAfter: response.headers.get('Retry-After') }
  }

  const client: RkgClient = {
    async listRepositories(params: ListParams = {}) {
      const { data } = await request('GET', '/repositories', {
        query: { q: params.q, offset: params.offset ?? 0, limit: params.limit ?? 20 },
      })
      return mapPage(data, mapRepository)
    },
    async getRepository(id) {
      const { data } = await request('GET', `/repositories/${encodeURIComponent(id)}`)
      return mapRepository(data)
    },
    async createRepository(body: RepositoryCreateBody) {
      const { data } = await request('POST', '/repositories', { body })
      return mapRepository(data)
    },
    async updateRepository(id, body: RepositoryUpdateBody) {
      const { data } = await request('PATCH', `/repositories/${encodeURIComponent(id)}`, { body })
      return mapRepository(data)
    },
    async deleteRepository(id) {
      await request('DELETE', `/repositories/${encodeURIComponent(id)}`)
    },
    async startIndexJob(repositoryId, body) {
      const { data, retryAfter } = await request(
        'POST',
        `/repositories/${encodeURIComponent(repositoryId)}/index-jobs`,
        { body: body ?? {} },
      )
      return mapJob(data, retryAfter).job
    },
    async getIndexJob(jobId) {
      const { data, retryAfter } = await request('GET', `/index-jobs/${encodeURIComponent(jobId)}`)
      return mapJob(data, retryAfter)
    },
    async listSnapshots(repositoryId, params = {}) {
      const { data } = await request(
        'GET',
        `/repositories/${encodeURIComponent(repositoryId)}/snapshots`,
        { query: { offset: params.offset ?? 0, limit: params.limit ?? 20 } },
      )
      return mapPage(data, mapSnapshot)
    },
    async getSnapshot(repositoryId, snapshotId) {
      const { data } = await request(
        'GET',
        `/repositories/${encodeURIComponent(repositoryId)}/snapshots/${encodeURIComponent(snapshotId)}`,
      )
      return mapSnapshot(data)
    },
    async activateSnapshot(repositoryId, snapshotId) {
      const { data } = await request(
        'POST',
        `/repositories/${encodeURIComponent(repositoryId)}/snapshots/${encodeURIComponent(snapshotId)}/activate`,
      )
      return mapRepository(data)
    },
    async deleteSnapshot(repositoryId, snapshotId) {
      await request(
        'DELETE',
        `/repositories/${encodeURIComponent(repositoryId)}/snapshots/${encodeURIComponent(snapshotId)}`,
      )
    },
    async searchEntities(snapshotId, params = {}) {
      if (params.type === 'interface') {
        return { items: [], page: { offset: params.offset ?? 0, limit: params.limit ?? 20, total: 0 } }
      }
      const { data } = await request('GET', '/entities', {
        query: {
          snapshot_id: snapshotId,
          q: params.q,
          type: domainEntityType(params.type),
          offset: params.offset ?? 0,
          limit: params.limit ?? 20,
        },
      })
      return mapPage(data, mapEntitySummary)
    },
    async getEntity(snapshotId, entityId) {
      const { data } = await request('GET', `/entities/${encodeURIComponent(entityId)}`, {
        query: { snapshot_id: snapshotId },
      })
      return mapEntityDetail(data)
    },
    async getSubgraph(params: SubgraphParams) {
      const { data } = await request('GET', '/subgraph', {
        query: {
          snapshot_id: params.snapshot_id,
          root_id: params.root_id,
          direction: params.direction,
          edge_types: params.edge_types,
          depth: params.depth,
          max_nodes: params.max_nodes,
          max_edges: params.max_edges,
          view: params.view,
          include_structure: params.include_structure === undefined ? undefined : String(params.include_structure),
          include_dependencies: params.include_dependencies === undefined ? undefined : String(params.include_dependencies),
        },
      })
      if (params.view === 'flow' && (!data || typeof data !== 'object' || !('view' in data) || data.view !== 'flow')) {
        throw new RkgApiError(409, 'graph_flow_unavailable', 'Backend đang chạy chưa hỗ trợ graph theo luồng. Hãy khởi động lại backend bằng code hiện tại rồi scan lại project.')
      }
      return mapSubgraph(data)
    },
    async listTechnologies(snapshotId) {
      const { data } = await request('GET', '/technologies', { query: { snapshot_id: snapshotId } })
      return Array.isArray(data) ? data.map(mapTechnology) : []
    },
    async listDependencies(snapshotId, params = {}) {
      const { data } = await request('GET', '/dependencies', {
        query: {
          snapshot_id: snapshotId,
          subtype: params.subtype,
          q: params.q,
          offset: params.offset ?? 0,
          limit: params.limit ?? 20,
        },
      })
      return mapPage(data, mapDependency)
    },
    async listDiagnostics(snapshotId, params = {}) {
      const { data } = await request('GET', '/diagnostics', {
        query: {
          snapshot_id: snapshotId,
          offset: params.offset ?? 0,
          limit: params.limit ?? 20,
        },
      })
      return mapPage(data, mapDiagnostic)
    },
    async exportContext(req: ContextRequest) {
      const { data } = await request('POST', '/context', { body: req })
      return mapContext(data)
    },
    async listConversations(params = {}) {
      const { data } = await request('GET', '/conversations', {
        query: {
          repository_id: params.repository_id,
          snapshot_id: params.snapshot_id,
          offset: params.offset ?? 0,
          limit: params.limit ?? 20,
        },
      })
      return mapPage(data, mapConversation)
    },
    async createConversation(body: ConversationCreateBody) {
      const { data } = await request('POST', '/conversations', { body })
      return mapConversation(data)
    },
    async getConversationCapabilities() {
      const { data } = await request('GET', '/conversations/capabilities')
      const value = data as ConversationCapabilities
      if (value.schema_version !== 'rkg.conversation-capabilities/1' || typeof value.provider_enabled !== 'boolean' || !Array.isArray(value.features)) throw new RkgApiError(502,'invalid_capabilities','Invalid capabilities.')
      return value
    },
    async getExactCitation(id: string, turnId: string, index: number) {
      const { data } = await request('GET', '/conversations/' + encodeURIComponent(id) + '/turns/' + encodeURIComponent(turnId) + '/citations/' + index)
      return data as ExactCitation
    },
    async getConversation(id: string, params: ListParams & { include_unavailable?: boolean } = {}) {
      const { data } = await request('GET', `/conversations/${encodeURIComponent(id)}/turns`, {
        query: { offset: params.offset ?? 0, limit: params.limit ?? 100, include_unavailable: params.include_unavailable === undefined ? undefined : String(params.include_unavailable) },
      })
      return mapConversationHistory(data)
    },
    async submitTurn(id: string, body: TurnSubmitBody) {
      const { data } = await request('POST', `/conversations/${encodeURIComponent(id)}/turns`, {
        body,
      })
      return mapTurnResult(data)
    },
    async deleteConversation(id: string) {
      await request('DELETE', `/conversations/${encodeURIComponent(id)}`)
    },
  }
  return client
}
