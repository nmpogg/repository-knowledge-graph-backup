import { describe, expect, it } from 'vitest'
import {
  endpointDisplayLabel,
  endpointEntryKind,
  flowPresetIdForEntry,
  isPartialUiFlow,
  outboundRequestsFromFlow,
  routeOutboundRequests,
  routeOutboundResponses,
  routePageHandler,
  routeSignal,
  snapshotSupportsApiToDb,
} from './endpointKind'

describe('endpointEntryKind', () => {
  it('classifies by attributes, not language', () => {
    expect(
      endpointEntryKind({
        id: '1',
        type: 'endpoint',
        name: '/orders',
        qualified_name: 'navigation:/orders',
        attributes: { kind: 'navigation', path: '/orders' },
      }),
    ).toBe('navigation')
    expect(
      endpointEntryKind({
        id: '2',
        type: 'endpoint',
        name: 'GET /api/orders',
        qualified_name: 'handler:GET:/api/orders',
        attributes: { method: 'GET', path: '/api/orders' },
      }),
    ).toBe('http')
  })

  it('labels HTTP and navigation endpoints for the list', () => {
    expect(
      endpointDisplayLabel({
        id: '1',
        type: 'endpoint',
        name: '/orders',
        qualified_name: 'navigation:/orders',
        attributes: { kind: 'navigation', path: '/orders' },
      }),
    ).toBe('/orders')
    expect(
      endpointDisplayLabel({
        id: '2',
        type: 'endpoint',
        name: 'get_order',
        qualified_name: 'app:get_order',
        attributes: { method: 'GET', path: '/api/orders' },
      }),
    ).toBe('GET /api/orders')
  })

  it('reads page handler and route signal attributes', () => {
    const entity = {
      id: '1',
      type: 'endpoint' as const,
      name: '/orders',
      qualified_name: 'navigation:/orders',
      attributes: {
        kind: 'navigation',
        path: '/orders',
        page_handler: 'OrdersPage',
        route_signal: 'outbound_http',
        outbound_requests:
          'GET /api/orders → VITE_API_BASE_URL | GET → https://inventory.example.test',
        outbound_responses: 'Order[] | ',
      },
    }
    expect(routePageHandler(entity)).toBe('OrdersPage')
    expect(routeSignal(entity)).toBe('outbound_http')
    expect(routeOutboundRequests(entity)).toEqual([
      'GET /api/orders → VITE_API_BASE_URL',
      'GET → https://inventory.example.test',
    ])
    expect(routeOutboundResponses(entity)).toEqual(['Order[]', ''])
    expect(flowPresetIdForEntry('navigation')).toBe('ui_to_api')
    expect(flowPresetIdForEntry('http')).toBe('api_to_db')
    expect(flowPresetIdForEntry('messaging')).toBe('topic_flow')
  })

  it('treats topic entities as messaging entrypoints', () => {
    expect(
      endpointEntryKind({
        id: 't1',
        type: 'topic',
        name: 'orders.events',
        qualified_name: 'orders.events',
        attributes: { channel_kind: 'topic', name: 'orders.events' },
      }),
    ).toBe('messaging')
    expect(
      endpointDisplayLabel({
        id: 't1',
        type: 'topic',
        name: 'orders.events',
        qualified_name: 'orders.events',
        attributes: { name: 'orders.events' },
      }),
    ).toBe('orders.events')
  })

  it('derives outbound request lines from a UI→API flow subgraph', () => {
    expect(
      outboundRequestsFromFlow(
        [
          { id: 'r', type: 'endpoint', label: '/orders', qualified_name: 'navigation:/orders' },
          {
            id: 'a',
            type: 'function',
            label: 'listOrders',
            qualified_name: 'OrderApi.listOrders',
            attributes: {
              http_requests: 'GET /api/orders',
              http_response_types: 'Order[]',
            },
          },
          {
            id: 'c',
            type: 'config',
            label: 'VITE_API_BASE_URL',
            qualified_name: 'environment:VITE_API_BASE_URL',
          },
          {
            id: 'x',
            type: 'dependency',
            label: 'https://inventory.example.test',
            qualified_name: 'https://inventory.example.test',
          },
        ],
        [
          { id: 'e1', source: 'a', target: 'c', type: 'depends_on', label: 'depends_on' },
          { id: 'e2', source: 'a', target: 'x', type: 'depends_on', label: 'depends_on' },
        ],
      ),
    ).toEqual([
      'GET /api/orders → VITE_API_BASE_URL',
      'GET /api/orders → https://inventory.example.test',
    ])
  })

  it('falls back to METHOD when path literal is absent but HTTP client call exists', () => {
    expect(
      outboundRequestsFromFlow(
        [
          {
            id: 'r',
            type: 'endpoint',
            label: '/orders/:orderId',
            qualified_name: 'navigation:/orders/:orderId',
          },
          {
            id: 'p',
            type: 'function',
            label: 'OrderDetailPage.OrderDetailPage',
            qualified_name: 'OrderDetailPage.OrderDetailPage',
          },
          {
            id: 'a',
            type: 'function',
            label: 'OrderApi.getOrder',
            qualified_name: 'OrderApi.getOrder',
            attributes: { http_requests: 'GET' },
          },
          {
            id: 'g',
            type: 'function',
            label: 'FetchHttpClient.get',
            qualified_name: 'FetchHttpClient.get',
          },
          {
            id: 'req',
            type: 'function',
            label: 'FetchHttpClient.request',
            qualified_name: 'FetchHttpClient.request',
          },
        ],
        [
          { id: 'e1', source: 'r', target: 'p', type: 'handled_by', label: 'handled_by' },
          { id: 'e2', source: 'p', target: 'a', type: 'calls', label: 'calls' },
          { id: 'e3', source: 'a', target: 'g', type: 'calls', label: 'calls' },
          { id: 'e4', source: 'g', target: 'req', type: 'calls', label: 'calls' },
        ],
      ),
    ).toEqual(['GET'])
  })

  it('falls back to METHOD from client leaf when http_requests is missing', () => {
    expect(
      outboundRequestsFromFlow(
        [
          {
            id: 'a',
            type: 'function',
            label: 'OrderApi.getOrder',
            qualified_name: 'OrderApi.getOrder',
          },
          {
            id: 'g',
            type: 'function',
            label: 'FetchHttpClient.get',
            qualified_name: 'FetchHttpClient.get',
          },
        ],
        [{ id: 'e3', source: 'a', target: 'g', type: 'calls', label: 'calls' }],
      ),
    ).toEqual(['GET'])
  })
  it('flags partial UI flows without call/depends chain', () => {
    expect(
      isPartialUiFlow(
        'navigation',
        [
          { id: 'r', type: 'endpoint', label: '/orders', qualified_name: 'navigation:/orders' },
          { id: 'p', type: 'function', label: 'OrdersPage', qualified_name: 'OrdersPage' },
        ],
        [{ id: 'e1', source: 'r', target: 'p', type: 'handled_by', label: 'handled_by' }],
      ),
    ).toBe(true)
    expect(
      isPartialUiFlow(
        'http',
        [
          { id: 'r', type: 'endpoint', label: 'GET /x', qualified_name: 'x' },
          { id: 'p', type: 'function', label: 'h', qualified_name: 'h' },
        ],
        [{ id: 'e1', source: 'r', target: 'p', type: 'handled_by', label: 'handled_by' }],
      ),
    ).toBe(false)
    expect(
      isPartialUiFlow(
        'navigation',
        [
          { id: 'r', type: 'endpoint', label: '/orders', qualified_name: 'navigation:/orders' },
          { id: 'p', type: 'function', label: 'OrdersPage', qualified_name: 'OrdersPage' },
          { id: 'a', type: 'function', label: 'listOrders', qualified_name: 'listOrders' },
        ],
        [
          { id: 'e1', source: 'r', target: 'p', type: 'handled_by', label: 'handled_by' },
          { id: 'e2', source: 'p', target: 'a', type: 'calls', label: 'calls' },
        ],
      ),
    ).toBe(false)
  })

  it('hides API→DB when snapshot has only UI routes and no data resources', () => {
    const nav = {
      id: '1',
      type: 'endpoint' as const,
      name: '/orders',
      qualified_name: 'navigation:/orders',
      attributes: { kind: 'navigation', path: '/orders' },
    }
    expect(snapshotSupportsApiToDb([nav], false)).toBe(false)
    expect(snapshotSupportsApiToDb([nav], true)).toBe(true)
    expect(
      snapshotSupportsApiToDb(
        [
          nav,
          {
            id: '2',
            type: 'endpoint',
            name: 'GET /api',
            qualified_name: 'api',
            attributes: { method: 'GET', path: '/api' },
          },
        ],
        false,
      ),
    ).toBe(true)
  })
})
