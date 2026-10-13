import { describe, expect, it } from 'vitest'
import type { GraphNode, GraphEdge } from '../../types/api'
import { flowPresentation } from './flowPresentation'
import { layoutGraph } from './graphLayout'

describe('flow ownership presentation', () => {
  const nodes: GraphNode[] = [
    { id: 'ep', type: 'endpoint', label: 'GET /cart', qualified_name: 'GET /cart' },
    { id: 'handler', type: 'function', label: 'handler', qualified_name: 'api.cart.handler', file_path: 'api/cart.py' },
    { id: 'repo', type: 'function', label: 'get', qualified_name: 'repos.CartRepository.get', file_path: 'repos/cart.py' },
    { id: 'db', type: 'table', label: 'carts', qualified_name: 'sqlalchemy::carts' },
    { id: 'file', type: 'file', label: 'cart.py', qualified_name: 'api.cart' },
    { id: 'folder', type: 'directory', label: 'api', qualified_name: 'api' },
  ]
  const edges: GraphEdge[] = [
    { id: 'a', source: 'ep', target: 'handler', type: 'handled_by', label: 'handled_by' },
    { id: 'b', source: 'handler', target: 'repo', type: 'calls', label: 'calls' },
    { id: 'c', source: 'repo', target: 'db', type: 'reads', label: 'reads' },
    { id: 'd', source: 'file', target: 'handler', type: 'contains', label: 'contains' },
    { id: 'e', source: 'folder', target: 'file', type: 'contains', label: 'contains' },
  ]
  it('shows ownership as optional breadcrumbs without moving or adding flow steps', () => {
    const plain = flowPresentation(nodes, edges, 'ep', false)
    const located = flowPresentation(nodes, edges, 'ep', true)
    expect(plain.nodes.map((node) => node.id)).toEqual(['ep', 'handler', 'repo', 'db'])
    expect(located.nodes.map((node) => node.id)).toEqual(plain.nodes.map((node) => node.id))
    expect(located.edges).toEqual(plain.edges)
    expect(located.nodes.find((node) => node.id === 'handler')!.location).toBe('api/cart.py')
    expect(plain.nodes.every((node) => !node.location)).toBe(true)
    expect(located.nodes.find((node) => node.id === 'repo')!.label).toBe('CartRepository.get')
    expect(layoutGraph(located.nodes, located.edges, 'ep', 'flow').map((node) => node.position))
      .toEqual(layoutGraph(plain.nodes, plain.edges, 'ep', 'flow').map((node) => node.position))
  })

  it('labels HTTP endpoints with METHOD path from attributes', () => {
    const httpNodes: GraphNode[] = [
      {
        id: 'ep',
        type: 'endpoint',
        label: 'get',
        qualified_name: 'api.OrderController.get',
        attributes: { method: 'GET', path: '/api/orders/{orderId}' },
      },
      { id: 'handler', type: 'function', label: 'get', qualified_name: 'api.OrderController.get' },
    ]
    const httpEdges: GraphEdge[] = [
      { id: 'a', source: 'ep', target: 'handler', type: 'handled_by', label: 'handled_by' },
    ]
    const presented = flowPresentation(httpNodes, httpEdges, 'ep', false)
    expect(presented.nodes.find((node) => node.id === 'ep')!.label).toBe(
      'GET /api/orders/{orderId}',
    )
  })

  it('labels navigation UI→API callables with evidence-based HTTP requests', () => {
    const navNodes: GraphNode[] = [
      {
        id: 'route',
        type: 'endpoint',
        label: '/orders',
        qualified_name: 'navigation:/orders',
        attributes: { kind: 'navigation', path: '/orders' },
      },
      {
        id: 'api',
        type: 'function',
        label: 'listOrders',
        qualified_name: 'OrderApi.listOrders',
        attributes: { http_requests: 'GET /api/orders', http_response_types: 'Order[]' },
      },
      {
        id: 'get',
        type: 'function',
        label: 'get',
        qualified_name: 'FetchHttpClient.get',
      },
    ]
    const navEdges: GraphEdge[] = [
      { id: 'a', source: 'route', target: 'api', type: 'calls', label: 'calls' },
      { id: 'b', source: 'api', target: 'get', type: 'calls', label: 'calls' },
    ]
    const presented = flowPresentation(navNodes, navEdges, 'route', false)
    expect(presented.nodes.find((node) => node.id === 'api')!.label).toBe('GET /api/orders')
    expect(presented.nodes.find((node) => node.id === 'get')!.label).toBe('GET')
    // HTTP API roots keep prior ownership labeling (no request rewrite).
    const httpRoot = flowPresentation(nodes, edges, 'ep', false)
    expect(httpRoot.nodes.find((node) => node.id === 'repo')!.label).toBe('CartRepository.get')
  })
})
