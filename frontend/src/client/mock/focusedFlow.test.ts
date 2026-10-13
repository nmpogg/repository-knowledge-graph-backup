import { describe, expect, it } from 'vitest'
import { createMockClient } from './mockClient'
import { DEMO_SNAPSHOT_ID } from './fixtures'

describe('focused flow mock contract', () => {
  it('reaches data without ownership and adds ownership without expanding it', async () => {
    const client = createMockClient()
    const params = { snapshot_id: DEMO_SNAPSHOT_ID, root_id: 'ent-endpoint-get-order', view: 'flow' as const, depth: 6 }
    const flow = await client.getSubgraph(params)
    expect(flow.nodes.some((n) => n.id === 'ent-table-orders')).toBe(true)
    expect(flow.nodes.some((n) => n.id === 'ent-class-order-repo')).toBe(false)
    expect(flow.nodes.some((n) => n.id === 'ent-config-db-url')).toBe(false)
    expect(flow.edges.some((e) => ['contains', 'imports', 'depends_on'].includes(e.type))).toBe(false)
    const overlay = await client.getSubgraph({ ...params, include_structure: true })
    expect(overlay.nodes.some((n) => n.id === 'ent-class-order-repo')).toBe(true)
    expect(overlay.nodes.some((n) => n.id === 'ent-iface-order-store')).toBe(false)
    expect(overlay.nodes.some((n) => n.id === 'ent-config-db-url')).toBe(false)
    const deps = await client.getSubgraph({ ...params, include_dependencies: true })
    expect(deps.nodes.some((n) => n.id === 'ent-config-db-url')).toBe(true)
  })
})
