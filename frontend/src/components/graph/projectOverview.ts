import type { RkgClient } from '../../client/mock/mockClient'
import type { EntitySummary, GraphEdge, GraphNode, SubgraphResponse } from '../../types/api'
import { endpointDisplayLabel } from '../../lib/endpointKind'

const STRUCTURAL = new Set(['directory', 'file'])
const HIDDEN_EDGES = new Set(['contains', 'imports'])
const ENTRY_CAP = 80

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

async function listAll(
  client: Pick<RkgClient, 'searchEntities'>,
  snapshotId: string,
  type: string,
  cap: number,
): Promise<{ items: EntitySummary[]; truncated: boolean }> {
  const items: EntitySummary[] = []
  let offset = 0
  let total = 0
  while (items.length < cap) {
    const page = await client.searchEntities(snapshotId, { type, limit: 100, offset })
    total = page.page.total
    items.push(...page.items)
    offset += page.items.length
    if (page.items.length === 0 || offset >= total) break
  }
  return { items: items.slice(0, cap), truncated: total > cap }
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

/** Snapshot-wide architecture map. Ignores the explorer selection and search list. */
export async function loadProjectOverview(
  client: Pick<RkgClient, 'searchEntities' | 'getSubgraph'>,
  snapshotId: string,
): Promise<SubgraphResponse> {
  const [endpoints, topics, tables, configs] = await Promise.all([
    listAll(client, snapshotId, 'endpoint', ENTRY_CAP),
    listAll(client, snapshotId, 'topic', ENTRY_CAP),
    listAll(client, snapshotId, 'table', 80),
    listAll(client, snapshotId, 'config', 40),
  ])
  const entries = [...endpoints.items, ...topics.items]
  const nodes = new Map<string, GraphNode>()
  const edges = new Map<string, GraphEdge>()
  let truncated = endpoints.truncated || topics.truncated || tables.truncated || configs.truncated

  const addGraph = (graph: SubgraphResponse) => {
    if (graph.truncated) truncated = true
    for (const node of graph.nodes) {
      if (STRUCTURAL.has(node.type)) continue
      nodes.set(node.id, node)
    }
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

  for (const entity of [...tables.items, ...configs.items]) {
    if (!nodes.has(entity.id)) nodes.set(entity.id, toNode(entity))
  }

  const keptEdges = [...edges.values()].filter((edge) => nodes.has(edge.source) && nodes.has(edge.target))
  const nodeList = [...nodes.values()].sort((a, b) => a.qualified_name.localeCompare(b.qualified_name) || a.id.localeCompare(b.id))
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
