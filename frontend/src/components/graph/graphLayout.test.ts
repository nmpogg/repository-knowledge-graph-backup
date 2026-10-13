import { describe, expect, it } from 'vitest'
import type { GraphEdge, GraphNode } from '../../types/api'
import { classifyFlowLayout, layoutGraph } from './graphLayout'

const nodes: GraphNode[] = [
  { id: 'endpoint', type: 'endpoint', label: 'GET /orders', qualified_name: 'GET /orders' },
  { id: 'handler', type: 'function', label: 'get_order', qualified_name: 'get_order' },
  { id: 'repo', type: 'class', label: 'OrderRepository', qualified_name: 'OrderRepository' },
  { id: 'table', type: 'table', label: 'orders', qualified_name: 'orders' },
]

const edges: GraphEdge[] = [
  { id: 'a', source: 'endpoint', target: 'handler', type: 'handled_by', label: 'handled_by' },
  { id: 'b', source: 'handler', target: 'repo', type: 'calls', label: 'calls' },
  { id: 'c', source: 'repo', target: 'table', type: 'reads', label: 'reads' },
]

describe('graph layout', () => {
  it('keeps calls forward and shared data last despite shortcut accesses', () => {
    const shortcut: GraphEdge = { id: 'shortcut', source: 'handler', target: 'table', type: 'reads', label: 'reads' }
    const positions = new Map(layoutGraph(nodes, [...edges, shortcut], 'endpoint', 'flow').map((node) => [node.id, node.position]))
    expect(positions.get('table')!.y).toBeGreaterThan(positions.get('repo')!.y)
    const extraCall: GraphEdge = { id: 'direct', source: 'endpoint', target: 'repo', type: 'calls', label: 'calls' }
    const direct = new Map(layoutGraph(nodes, [...edges, extraCall], 'endpoint', 'flow').map((node) => [node.id, node.position]))
    expect(direct.get('repo')!.y).toBeGreaterThan(direct.get('handler')!.y)
  })

  it('lays upstream resource users out as caller to database, rather than a disconnected column', () => {
    const positions = new Map(layoutGraph(nodes, edges, 'table', 'flow').map((node) => [node.id, node.position]))
    expect(positions.get('endpoint')!.y).toBeLessThan(positions.get('handler')!.y)
    expect(positions.get('handler')!.y).toBeLessThan(positions.get('repo')!.y)
    expect(positions.get('repo')!.y).toBeLessThan(positions.get('table')!.y)
  })

  it('keeps recursive calls finite, deterministic and ahead of their data access', () => {
    const recursive: GraphEdge = { id: 'recursive', source: 'repo', target: 'handler', type: 'calls', label: 'calls' }
    const result = layoutGraph(nodes, [...edges, recursive], 'endpoint', 'flow')
    expect(result).toEqual(layoutGraph([...nodes].reverse(), [...edges, recursive].reverse(), 'endpoint', 'flow'))
    expect(result.every((node) => Number.isFinite(node.position.x))).toBe(true)
    expect(result.find((node) => node.id === 'table')!.position.y).toBeGreaterThan(result.find((node) => node.id === 'repo')!.position.y)
  })

  it('places the API to DB path in readable top-to-bottom stages', () => {
    const positions = new Map(layoutGraph(nodes, edges, 'endpoint', 'flow').map((node) => [node.id, node.position]))
    expect(positions.get('endpoint')?.y).toBe(0)
    expect(positions.get('handler')!.y).toBeGreaterThan(positions.get('endpoint')!.y)
    expect(positions.get('repo')!.y).toBeGreaterThan(positions.get('handler')!.y)
    expect(positions.get('table')!.y).toBeGreaterThan(positions.get('repo')!.y)
  })

  it('still lays out nodes when the requested root is not in the graph', () => {
    const result = layoutGraph(nodes, edges, 'missing-root')
    expect(result.map((node) => node.id).sort()).toEqual(nodes.map((node) => node.id).sort())
    expect(result.every((node) => Number.isFinite(node.position.x) && Number.isFinite(node.position.y))).toBe(true)
  })

  it('keeps every architecture node at a distinct position, including disconnected nodes', () => {
    const extra = { id: 'isolated', type: 'config' as const, label: 'config', qualified_name: 'config' }
    const result = layoutGraph([extra, ...nodes], edges, 'repo')
    const positions = result.map((node) => `${node.position.x}:${node.position.y}`)
    expect(new Set(positions).size).toBe(result.length)
    const y = new Map(result.map((node) => [node.id, node.position.y]))
    expect(y.get('endpoint')!).toBeLessThan(y.get('handler')!)
    expect(y.get('handler')!).toBeLessThan(y.get('repo')!)
    expect(y.get('repo')!).toBeLessThan(y.get('table')!)
    expect(y.get('table')!).toBeLessThan(y.get('isolated')!)
    expect(new Set(result.map((node) => node.data.layer)).size).toBeGreaterThanOrEqual(5)
  })

  it('wraps a wide architecture layer onto extra rows instead of one endless line', () => {
    const wide: GraphNode[] = [
      { id: 'root', type: 'directory', label: 'src', qualified_name: 'src' },
      ...Array.from({ length: 8 }, (_, index) => ({
        id: `file-${index}`,
        type: 'file' as const,
        label: `file-${index}`,
        qualified_name: `file-${index}`,
      })),
    ]
    const wideEdges: GraphEdge[] = wide.slice(1).map((node) => ({
      id: `c-${node.id}`,
      source: 'root',
      target: node.id,
      type: 'contains' as const,
      label: 'contains',
    }))
    const placed = layoutGraph(wide, wideEdges, 'root', 'architecture')
    const files = placed.filter((node) => node.id.startsWith('file-'))
    const ys = new Set(files.map((node) => node.position.y))
    expect(ys.size).toBeGreaterThan(1)
    expect(placed.find((node) => node.id === 'root')!.position.y).toBeLessThan(Math.min(...files.map((node) => node.position.y)))
  })

  it('places each project entry in its own column and shared tables underneath', () => {
    const project: GraphNode[] = [
      { id: 'get', type: 'endpoint', label: 'GET /orders', qualified_name: 'GET /orders' },
      { id: 'post', type: 'endpoint', label: 'POST /orders', qualified_name: 'POST /orders' },
      { id: 'load', type: 'function', label: 'load_order', qualified_name: 'load_order' },
      { id: 'save', type: 'function', label: 'save_order', qualified_name: 'save_order' },
      { id: 'orders', type: 'table', label: 'orders', qualified_name: 'orders' },
    ]
    const projectEdges: GraphEdge[] = [
      { id: 'h1', source: 'get', target: 'load', type: 'handled_by', label: 'handled_by' },
      { id: 'h2', source: 'post', target: 'save', type: 'handled_by', label: 'handled_by' },
      { id: 'r', source: 'load', target: 'orders', type: 'reads', label: 'reads' },
      { id: 'w', source: 'save', target: 'orders', type: 'writes', label: 'writes' },
    ]
    const positions = new Map(
      layoutGraph(project, projectEdges, 'get', 'architecture').map((node) => [node.id, node.position]),
    )
    expect(positions.get('get')!.y).toBe(positions.get('post')!.y)
    expect(positions.get('get')!.x).not.toBe(positions.get('post')!.x)
    expect(positions.get('load')!.x).toBe(positions.get('get')!.x)
    expect(positions.get('save')!.x).toBe(positions.get('post')!.x)
    expect(positions.get('load')!.y).toBeGreaterThan(positions.get('get')!.y)
    expect(positions.get('orders')!.y).toBeGreaterThan(positions.get('load')!.y)
    expect(positions.get('orders')!.y).toBeGreaterThan(positions.get('save')!.y)
  })

  it('splits topic publishers and consumers onto opposite sides of the hub', () => {
    const topicNodes: GraphNode[] = [
      { id: 'topic', type: 'topic', label: 'order-processing', qualified_name: 'order-processing' },
      { id: 'pub-a', type: 'function', label: 'publishA', qualified_name: 'publishA' },
      { id: 'pub-b', type: 'function', label: 'publishB', qualified_name: 'publishB' },
      { id: 'con-a', type: 'function', label: 'consumeA', qualified_name: 'consumeA' },
      { id: 'con-b', type: 'function', label: 'consumeB', qualified_name: 'consumeB' },
    ]
    const topicEdges: GraphEdge[] = [
      { id: 'p1', source: 'pub-a', target: 'topic', type: 'publishes', label: 'publishes' },
      { id: 'p2', source: 'pub-b', target: 'topic', type: 'publishes', label: 'publishes' },
      { id: 'c1', source: 'con-a', target: 'topic', type: 'consumes', label: 'consumes' },
      { id: 'c2', source: 'con-b', target: 'topic', type: 'consumes', label: 'consumes' },
    ]
    expect(classifyFlowLayout(topicNodes, topicEdges, 'topic').kind).toBe('hub_opposing')
    const positions = new Map(
      layoutGraph(topicNodes, topicEdges, 'topic', 'flow').map((node) => [node.id, node.position]),
    )
    const hubX = positions.get('topic')!.x
    expect(positions.get('pub-a')!.x).toBeLessThan(hubX)
    expect(positions.get('pub-b')!.x).toBeLessThan(hubX)
    expect(positions.get('con-a')!.x).toBeGreaterThan(hubX)
    expect(positions.get('con-b')!.x).toBeGreaterThan(hubX)
    expect(positions.get('pub-a')!.x).toBe(positions.get('pub-b')!.x)
    expect(positions.get('con-a')!.x).toBe(positions.get('con-b')!.x)
    // Deterministic across input shuffle.
    expect(layoutGraph(topicNodes, topicEdges, 'topic', 'flow')).toEqual(
      layoutGraph([...topicNodes].reverse(), [...topicEdges].reverse(), 'topic', 'flow'),
    )
  })

  it('keeps topic-flow downstream under the consumer wing without collapsing role sides', () => {
    const topicNodes: GraphNode[] = [
      { id: 'topic', type: 'topic', label: 'orders', qualified_name: 'orders' },
      { id: 'publisher', type: 'function', label: 'publish', qualified_name: 'publish' },
      { id: 'consumer', type: 'function', label: 'consume', qualified_name: 'consume' },
      { id: 'handler', type: 'function', label: 'handle', qualified_name: 'handle' },
      { id: 'table', type: 'table', label: 'orders', qualified_name: 'sql::orders' },
    ]
    const topicEdges: GraphEdge[] = [
      { id: 'p', source: 'publisher', target: 'topic', type: 'publishes', label: 'publishes' },
      { id: 'c', source: 'consumer', target: 'topic', type: 'consumes', label: 'consumes' },
      { id: 'call', source: 'consumer', target: 'handler', type: 'calls', label: 'calls' },
      { id: 'r', source: 'handler', target: 'table', type: 'reads', label: 'reads' },
    ]
    const positions = new Map(
      layoutGraph(topicNodes, topicEdges, 'topic', 'flow').map((node) => [node.id, node.position]),
    )
    expect(positions.get('publisher')!.x).toBeLessThan(positions.get('topic')!.x)
    expect(positions.get('consumer')!.x).toBeGreaterThan(positions.get('topic')!.x)
    expect(positions.get('handler')!.y).toBeGreaterThan(positions.get('consumer')!.y)
    expect(positions.get('table')!.y).toBeGreaterThan(positions.get('handler')!.y)
    expect(positions.get('handler')!.x).toBeGreaterThan(positions.get('topic')!.x)
  })

  it('splits reads vs writes wings when a pipeline tier has enough distinct roles', () => {
    const dataNodes: GraphNode[] = [
      { id: 'endpoint', type: 'endpoint', label: 'POST /orders', qualified_name: 'POST /orders' },
      { id: 'reader', type: 'function', label: 'load', qualified_name: 'load' },
      { id: 'writer', type: 'function', label: 'save', qualified_name: 'save' },
      { id: 'auditor', type: 'function', label: 'audit', qualified_name: 'audit' },
      { id: 'table', type: 'table', label: 'orders', qualified_name: 'orders' },
    ]
    const dataEdges: GraphEdge[] = [
      { id: 'h1', source: 'endpoint', target: 'reader', type: 'handled_by', label: 'handled_by' },
      { id: 'h2', source: 'endpoint', target: 'writer', type: 'calls', label: 'calls' },
      { id: 'h3', source: 'endpoint', target: 'auditor', type: 'calls', label: 'calls' },
      { id: 'r', source: 'reader', target: 'table', type: 'reads', label: 'reads' },
      { id: 'w', source: 'writer', target: 'table', type: 'writes', label: 'writes' },
      { id: 'a', source: 'auditor', target: 'table', type: 'reads', label: 'reads' },
    ]
    const positions = new Map(
      layoutGraph(dataNodes, dataEdges, 'endpoint', 'flow').map((node) => [node.id, node.position]),
    )
    expect(positions.get('endpoint')!.y).toBeLessThan(positions.get('reader')!.y)
    expect(positions.get('table')!.y).toBeGreaterThan(positions.get('reader')!.y)
    // readers and writer sit on opposite role wings, not one mixed cluster.
    expect(positions.get('reader')!.x).toBeLessThan(positions.get('writer')!.x)
    expect(positions.get('auditor')!.x).toBeLessThan(positions.get('writer')!.x)
  })

  it('keeps a simple call-chain deterministic without over-splitting small tiers', () => {
    const positions = new Map(layoutGraph(nodes, edges, 'endpoint', 'flow').map((node) => [node.id, node.position]))
    expect(positions.get('endpoint')!.x).toBe(0)
    expect(positions.get('handler')!.x).toBe(0)
    expect(positions.get('repo')!.x).toBe(0)
    expect(positions.get('table')!.x).toBe(0)
    expect(layoutGraph(nodes, edges, 'endpoint', 'flow')).toEqual(
      layoutGraph([...nodes].reverse(), [...edges].reverse(), 'endpoint', 'flow'),
    )
  })

  it('clusters config dependents above the hub without overlapping', () => {
    const configNodes: GraphNode[] = [
      { id: 'config', type: 'config', label: 'DB_URL', qualified_name: 'DB_URL' },
      { id: 'svc-a', type: 'function', label: 'ServiceA', qualified_name: 'ServiceA' },
      { id: 'svc-b', type: 'class', label: 'ServiceB', qualified_name: 'ServiceB' },
      { id: 'svc-c', type: 'function', label: 'ServiceC', qualified_name: 'ServiceC' },
    ]
    const configEdges: GraphEdge[] = [
      { id: 'd1', source: 'svc-a', target: 'config', type: 'depends_on', label: 'depends_on' },
      { id: 'd2', source: 'svc-b', target: 'config', type: 'depends_on', label: 'depends_on' },
      { id: 'd3', source: 'svc-c', target: 'config', type: 'depends_on', label: 'depends_on' },
    ]
    expect(classifyFlowLayout(configNodes, configEdges, 'config').kind).toBe('fan_in')
    const result = layoutGraph(configNodes, configEdges, 'config', 'flow')
    const positions = new Map(result.map((node) => [node.id, node.position]))
    expect(positions.get('config')!.y).toBe(0)
    for (const id of ['svc-a', 'svc-b', 'svc-c']) {
      expect(positions.get(id)!.y).toBeLessThan(positions.get('config')!.y)
    }
    const keys = result.map((node) => `${node.position.x}:${node.position.y}`)
    expect(new Set(keys).size).toBe(result.length)
  })

  it('separates interface implementors and inheritors into distinct clusters when both exist', () => {
    const ifaceNodes: GraphNode[] = [
      { id: 'iface', type: 'interface', label: 'Store', qualified_name: 'Store' },
      { id: 'impl-a', type: 'class', label: 'PgStore', qualified_name: 'PgStore' },
      { id: 'impl-b', type: 'class', label: 'MemStore', qualified_name: 'MemStore' },
      { id: 'base', type: 'class', label: 'AbstractStore', qualified_name: 'AbstractStore' },
    ]
    const ifaceEdges: GraphEdge[] = [
      { id: 'i1', source: 'impl-a', target: 'iface', type: 'implements', label: 'implements' },
      { id: 'i2', source: 'impl-b', target: 'iface', type: 'implements', label: 'implements' },
      { id: 'h1', source: 'base', target: 'iface', type: 'inherits_from', label: 'inherits_from' },
    ]
    expect(classifyFlowLayout(ifaceNodes, ifaceEdges, 'iface').kind).toBe('fan_in')
    const positions = new Map(
      layoutGraph(ifaceNodes, ifaceEdges, 'iface', 'flow').map((node) => [node.id, node.position]),
    )
    expect(positions.get('impl-a')!.x).toBe(positions.get('impl-b')!.x)
    expect(positions.get('impl-a')!.x).not.toBe(positions.get('base')!.x)
    expect(positions.get('iface')!.y).toBe(0)
    expect(positions.get('impl-a')!.y).toBeLessThan(0)
  })
})
