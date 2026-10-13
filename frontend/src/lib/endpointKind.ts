import type { EntitySummary, GraphEdge, GraphNode } from '../types/api'

/** Entrypoint shape from entity attributes — never from language/stack guesses. */
export type EndpointEntryKind = 'http' | 'navigation' | 'messaging' | 'other'

/** Evidence-based List signal from adapter attributes (OQ-RKG-007). */
export type RouteSignal = 'outbound_http' | 'shell' | 'partial' | null

export function endpointEntryKind(entity: EntitySummary): EndpointEntryKind {
  if (entity.type === 'topic') return 'messaging'
  const attrs = entity.attributes ?? {}
  if (attrs.kind === 'navigation') return 'navigation'
  if (typeof attrs.method === 'string' && attrs.method) return 'http'
  if (entity.qualified_name.startsWith('navigation:')) return 'navigation'
  // FastAPI-style display name "GET /path" without attributes (mock fixtures).
  if (/^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+\//i.test(entity.name)) return 'http'
  return 'other'
}

export function endpointDisplayLabel(entity: EntitySummary): string {
  const attrs = entity.attributes ?? {}
  const path =
    (typeof attrs.path === 'string' && attrs.path) ||
    (typeof attrs.route_path === 'string' && attrs.route_path) ||
    null
  const method = typeof attrs.method === 'string' ? attrs.method : null
  if (endpointEntryKind(entity) === 'messaging') {
    const topic =
      (typeof attrs.name === 'string' && attrs.name) ||
      entity.qualified_name ||
      entity.name
    return topic
  }
  if (endpointEntryKind(entity) === 'navigation') {
    return path || entity.name
  }
  if (method && path) return `${method} ${path}`
  return entity.name
}

export function routePageHandler(entity: EntitySummary): string | null {
  const handler = entity.attributes?.page_handler
  return typeof handler === 'string' && handler ? handler : null
}

export function routeSignal(entity: EntitySummary): RouteSignal {
  const signal = entity.attributes?.route_signal
  if (signal === 'outbound_http' || signal === 'shell' || signal === 'partial') {
    return signal
  }
  return null
}

/** Outbound request lines from adapter attribute `outbound_requests` ("a → b | c → d"). */
export function routeOutboundRequests(entity: EntitySummary): string[] {
  const raw = entity.attributes?.outbound_requests
  if (typeof raw !== 'string' || !raw.trim()) return []
  return raw
    .split('|')
    .map((part) => part.trim())
    .filter(Boolean)
}

/** Parallel response-type lines from `outbound_responses` (same pipe slots; empty = unknown). */
export function routeOutboundResponses(entity: EntitySummary): string[] {
  const raw = entity.attributes?.outbound_responses
  if (typeof raw !== 'string' || !raw.trim()) return []
  return raw.split('|').map((part) => part.trim())
}

const HTTP_CLIENT_METHODS = new Set([
  'get',
  'put',
  'post',
  'patch',
  'delete',
  'request',
  'fetch',
])

function shortFlowLabel(node: GraphNode): string {
  if (node.type === 'config' && node.qualified_name.includes(':')) {
    return node.qualified_name.split(':').slice(1).join(':')
  }
  if (node.type === 'dependency') {
    if (/^https?:\/\//i.test(node.qualified_name)) return node.qualified_name
    if (/^https?:\/\//i.test(node.label)) return node.label
  }
  const label = node.label || node.qualified_name
  const leaf = label.includes('.') ? label.split('.').pop()! : label
  return leaf
}

function isHttpClientMethod(node: GraphNode): boolean {
  return HTTP_CLIENT_METHODS.has(shortFlowLabel(node).toLowerCase())
}

function splitAttrLines(raw: string | undefined): string[] {
  if (!raw?.trim()) return []
  return raw
    .split('|')
    .map((part) => part.trim())
    .filter(Boolean)
}

function nodeHttpRequests(node: GraphNode): string[] {
  return splitAttrLines(node.attributes?.http_requests)
}

/**
 * Derive List request lines from a UI→API flow subgraph.
 * Prefer callable `http_requests` (method + path); else depends_on terminals;
 * else API → HTTP client method name as METHOD.
 */
export function outboundRequestsFromFlow(
  nodes: GraphNode[],
  edges: GraphEdge[],
): string[] {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const lines: string[] = []
  const seen = new Set<string>()
  const push = (line: string) => {
    if (seen.has(line) || lines.length >= 12) return
    seen.add(line)
    lines.push(line)
  }

  const outgoing = new Map<string, GraphEdge[]>()
  for (const edge of edges) {
    const group = outgoing.get(edge.source) ?? []
    group.push(edge)
    outgoing.set(edge.source, group)
  }

  for (const node of nodes) {
    if (node.type !== 'function' || isHttpClientMethod(node)) continue
    const requests = nodeHttpRequests(node)
    if (requests.length === 0) continue
    const terminals: string[] = []
    for (const edge of outgoing.get(node.id) ?? []) {
      if (edge.type !== 'depends_on') continue
      const target = byId.get(edge.target)
      if (!target || (target.type !== 'dependency' && target.type !== 'config')) {
        continue
      }
      terminals.push(shortFlowLabel(target))
    }
    for (const req of requests) {
      if (terminals.length > 0) {
        for (const terminal of terminals) push(`${req} → ${terminal}`)
      } else {
        push(req)
      }
    }
  }
  if (lines.length > 0) return lines

  for (const edge of edges) {
    if (edge.type !== 'depends_on') continue
    const target = byId.get(edge.target)
    if (!target || (target.type !== 'dependency' && target.type !== 'config')) {
      continue
    }
    const source = byId.get(edge.source)
    push(`${source ? shortFlowLabel(source) : '?'} → ${shortFlowLabel(target)}`)
  }
  if (lines.length > 0) return lines

  for (const edge of edges) {
    if (edge.type !== 'calls') continue
    const target = byId.get(edge.target)
    const source = byId.get(edge.source)
    if (!target || !source || !isHttpClientMethod(target)) continue
    // Skip internal client chain get → request.
    if (isHttpClientMethod(source)) continue
    const fromAttrs = nodeHttpRequests(source)
    if (fromAttrs.length > 0) {
      for (const req of fromAttrs) push(req)
      continue
    }
    const method = shortFlowLabel(target).toUpperCase()
    if (method !== 'REQUEST' && method !== 'FETCH') {
      push(method)
    } else {
      push(`${shortFlowLabel(source)} → ${shortFlowLabel(target)}`)
    }
  }
  return lines
}

/** Response types parallel to outboundRequestsFromFlow when attributes carry them. */
export function outboundResponsesFromFlow(nodes: GraphNode[]): string[] {
  const lines: string[] = []
  for (const node of nodes) {
    if (node.type !== 'function' || isHttpClientMethod(node)) continue
    const requests = nodeHttpRequests(node)
    if (requests.length === 0) continue
    const responses = splitAttrLines(node.attributes?.http_response_types)
    for (let i = 0; i < requests.length; i++) {
      lines.push(responses[i] ?? '')
    }
  }
  return lines
}

/** Preset id for opening a List entry as Graph flow. */
export function flowPresetIdForEntry(
  kind: EndpointEntryKind,
): 'api_to_db' | 'ui_to_api' | 'topic_flow' {
  if (kind === 'navigation') return 'ui_to_api'
  if (kind === 'messaging') return 'topic_flow'
  return 'api_to_db'
}

/**
 * Partial UI flow: navigation root with only handled_by (route → page), no call chain.
 * Does not apply to HTTP API endpoints.
 */
export function isPartialUiFlow(
  kind: EndpointEntryKind,
  nodes: GraphNode[],
  edges: GraphEdge[],
): boolean {
  if (kind !== 'navigation') return false
  const semantic = edges.filter(
    (edge) => edge.type !== 'contains' && edge.type !== 'imports',
  )
  if (semantic.length === 0) return true
  const hasChain = semantic.some(
    (edge) => edge.type === 'calls' || edge.type === 'depends_on',
  )
  if (hasChain) return false
  const onlyHandledBy = semantic.every((edge) => edge.type === 'handled_by')
  return onlyHandledBy && nodes.length <= 3
}

/** Snapshot has DataResource-like entities → API→DB preset is meaningful. */
export function snapshotSupportsApiToDb(
  endpoints: EntitySummary[],
  hasDataResource: boolean,
): boolean {
  if (hasDataResource) return true
  return endpoints.some((item) => endpointEntryKind(item) === 'http')
}
