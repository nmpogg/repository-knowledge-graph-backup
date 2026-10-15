import { describe, expect, it } from 'vitest'
import { DEMO_REPO_ID, DEMO_SNAPSHOT_ID, seedEntities, seedGraphEdges } from '../../client/mock/fixtures'
import { createMockClient } from '../../client/mock/mockClient'
import { PROJECT_OVERVIEW_ROOT_ID, exportProjectOverview, loadProjectOverview } from './projectOverview'

describe('loadProjectOverview', () => {
  it('returns every snapshot entry and does not root the diagram at one endpoint', async () => {
    const client = createMockClient()
    const roots: string[] = []
    const original = client.getSubgraph.bind(client)
    client.getSubgraph = async (params) => {
      roots.push(params.root_id)
      return original(params)
    }

    const graph = await loadProjectOverview(client, DEMO_SNAPSHOT_ID)

    expect(graph.root_id).toBe(PROJECT_OVERVIEW_ROOT_ID)
    expect(graph.root_id).not.toBe('ent-endpoint-get-order')
    expect(roots).toEqual(expect.arrayContaining([
      'ent-endpoint-get-order',
      'ent-topic-order-events',
    ]))
    expect(graph.nodes.map((node) => node.id).sort()).toEqual(seedEntities.map((entity) => entity.id).sort())
  }, 15000)

  it('exports every relationship without truncation', async () => {
    const client = createMockClient()
    const file = await exportProjectOverview(client, DEMO_SNAPSHOT_ID, DEMO_REPO_ID)

    expect(file.truncated).toBe(false)
    expect(file.truncation_reasons).toEqual([])
    expect(file.edges.map((edge) => edge.id).sort()).toEqual(seedGraphEdges.map((edge) => edge.id).sort())
    for (const edge of seedGraphEdges) {
      expect(file.edges).toEqual(expect.arrayContaining([
        expect.objectContaining({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          label: edge.label,
        }),
      ]))
    }
    expect(file.nodes.map((node) => node.id)).toEqual(expect.arrayContaining(seedGraphEdges.flatMap((edge) => [edge.source, edge.target])))
  }, 20000)
})
