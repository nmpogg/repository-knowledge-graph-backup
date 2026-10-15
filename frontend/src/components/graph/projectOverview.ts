import type { RkgClient } from '../../client/mock/mockClient'
import { endpointDisplayLabel } from '../../lib/endpointKind'
import type { EntitySummary, GraphEdge, GraphNode, SubgraphResponse } from '../../types/api'

export interface OverviewExportFile {
  schema_version: 'rkg.project-overview/1'
  repository_id: string
  snapshot_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  truncated: boolean
  truncation_reasons: string[]
}

const HIDDEN_EDGES = new Set(['contains', 'imports'])

/** Not a snapshot entity. Architecture fit uses this so the camera is not pinned to one endpoint. */
export const PROJECT_OVERVIEW_ROOT_ID = 'project-overview'

function toNode(entity: EntitySummary): GraphNode {
  return {
    id: entity.id,
    type: entity.type,
    label: entity.type === 'endpoint' || entity.type === 'topic' ? endpointDisplayLabel(entity) : entity.name,
    qualified_name: entity.qualified_name,
    file_path: entity.file_path,
    attributes: entity.attributes,
  }
}

async function mapPool<T>(items: T[], limit: number, run: (item: T) => Promise<void>) {
  let cursor = 0
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (cursor < items.length) {
      const index = cursor
      cursor += 1
      await run(items[index]!)
    }
  })
  await Promise.all(workers)
}

/** Snapshot-wide architecture map. Every entity is shown; selection and search do not filter it. */
export async function loadProjectOverview(
  client: Pick<RkgClient, 'searchEntities' | 'getSubgraph'>,
  snapshotId: string,
): Promise<SubgraphResponse> {
  const everyone = await listEvery(client, snapshotId)
  const entries = everyone.filter((entity) => entity.type === 'endpoint' || entity.type === 'topic')
  const nodes = new Map<string, GraphNode>()
  const edges = new Map<string, GraphEdge>()
  let truncated = false
  for (const entity of everyone) nodes.set(entity.id, toNode(entity))

  const addGraph = (graph: SubgraphResponse) => {
    if (graph.truncated) truncated = true
    for (const node of graph.nodes) nodes.set(node.id, node)
    for (const edge of graph.edges) {
      if (HIDDEN_EDGES.has(edge.type)) continue
      edges.set(edge.id, edge)
    }
  }

  await mapPool(entries, 4, async (entry) => {
    try {
      const graph = await client.getSubgraph({
        snapshot_id: snapshotId,
        root_id: entry.id,
        direction: entry.type === 'topic' ? 'both' : 'outgoing',
        edge_types: entry.type === 'topic'
          ? ['publishes', 'consumes', 'calls', 'reads', 'writes', 'depends_on']
          : undefined,
        depth: 6,
        max_nodes: 40,
        max_edges: 80,
        view: entry.type === 'topic' ? 'neighborhood' : 'flow',
        include_structure: false,
        include_dependencies: true,
      })
      addGraph(graph)
    } catch {
      truncated = true
    }
    nodes.set(entry.id, toNode(entry))
  })

  const keptEdges = [...edges.values()].filter((edge) => nodes.has(edge.source) && nodes.has(edge.target))
  const nodeList = [...nodes.values()].sort(byIdentity)
  return {
    snapshot_id: snapshotId,
    root_id: PROJECT_OVERVIEW_ROOT_ID,
    view: 'neighborhood',
    nodes: nodeList,
    edges: keptEdges,
    truncated,
    truncation_reasons: truncated ? ['max_nodes'] : [],
    limits: { depth: 6, max_nodes: nodeList.length, max_edges: keptEdges.length },
  }
}

function byIdentity(a: { qualified_name?: string; id: string }, b: { qualified_name?: string; id: string }) {
  return (a.qualified_name ?? '').localeCompare(b.qualified_name ?? '') || a.id.localeCompare(b.id)
}

async function listEvery(
  client: Pick<RkgClient, 'searchEntities'>,
  snapshotId: string,
): Promise<EntitySummary[]> {
  const items: EntitySummary[] = []
  let offset = 0
  let total = Number.POSITIVE_INFINITY
  while (offset < total) {
    const page = await client.searchEntities(snapshotId, { limit: 100, offset })
    total = page.page.total
    items.push(...page.items)
    if (page.items.length === 0) break
    offset += page.items.length
  }
  return items
}

/**
 * Every snapshot relationship, both directions, with no display cap.
 * Depth 1 from each entity keeps incident edges; max_nodes/max_edges stops are the only truncation.
 */
export async function exportProjectOverview(
  client: Pick<RkgClient, 'searchEntities' | 'getSubgraph'>,
  snapshotId: string,
  repositoryId: string,
): Promise<OverviewExportFile> {
  const entities = await listEvery(client, snapshotId)
  const nodes = new Map<string, GraphNode>()
  for (const entity of entities) nodes.set(entity.id, toNode(entity))
  const edges = new Map<string, GraphEdge>()
  const reasons = new Set<string>()

  await mapPool(entities, 4, async (entity) => {
    const graph = await client.getSubgraph({
      snapshot_id: snapshotId,
      root_id: entity.id,
      direction: 'both',
      depth: 1,
      max_nodes: 200,
      max_edges: 400,
      view: 'neighborhood',
    })
    for (const reason of graph.truncation_reasons) {
      if (reason === 'max_nodes' || reason === 'max_edges' || reason === 'budget_reached') {
        reasons.add(reason)
      }
    }
    for (const node of graph.nodes) {
      const listed = nodes.get(node.id)
      if (!listed) nodes.set(node.id, node)
      else if (node.location && !listed.location) nodes.set(node.id, { ...listed, location: node.location })
    }
    for (const edge of graph.edges) edges.set(edge.id, edge)
  })

  const edgeList = [...edges.values()].sort(
    (a, b) => a.type.localeCompare(b.type) || a.source.localeCompare(b.source) || a.target.localeCompare(b.target) || a.id.localeCompare(b.id),
  )
  return {
    schema_version: 'rkg.project-overview/1',
    repository_id: repositoryId,
    snapshot_id: snapshotId,
    nodes: [...nodes.values()].sort(byIdentity),
    edges: edgeList,
    truncated: reasons.size > 0,
    truncation_reasons: [...reasons].sort(),
  }
}
