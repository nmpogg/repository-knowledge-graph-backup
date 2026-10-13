import { describe, expect, it } from 'vitest'
import { DEMO_SNAPSHOT_ID } from '../../client/mock/fixtures'
import { createMockClient } from '../../client/mock/mockClient'
import { PROJECT_OVERVIEW_ROOT_ID, loadProjectOverview } from './projectOverview'

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
    expect(graph.nodes.map((node) => node.id)).toEqual(expect.arrayContaining([
      'ent-endpoint-get-order',
      'ent-topic-order-events',
      'ent-fn-consume-order',
      'ent-table-orders',
      'ent-config-db-url',
    ]))
  }, 15000)
})
