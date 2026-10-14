import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { DEMO_SNAPSHOT_ID } from '../../client/mock/fixtures'
import type { SubgraphParams } from '../../client/mock/mockClient'
import { AnnouncerProvider } from '../../components/ui/Announcer'
import { LocaleProvider } from '../../i18n'
import { ExplorerPage } from './ExplorerPage'

const SELECTED_ENDPOINT = 'ent-endpoint-get-order'

function endpointScopedCall(params: SubgraphParams) {
  return params.root_id === SELECTED_ENDPOINT && params.max_edges == null
}

afterEach(() => {
  cleanup()
  localStorage.removeItem('rkg-locale')
  vi.unstubAllGlobals()
})

function LocationProbe() {
  const location = useLocation()
  return <span data-testid="app-location">{location.pathname}</span>
}

function renderExplorer() {
  return render(
    <LocaleProvider>
      <AnnouncerProvider>
        <MemoryRouter initialEntries={[`/explorer?snapshot_id=${DEMO_SNAPSHOT_ID}`]}>
          <LocationProbe />
          <Routes>
            <Route path="/explorer" element={<ExplorerPage />} />
            <Route path="/conversations" element={<h1>Ask page</h1>} />
            <Route path="/conversations/:conversationId" element={<h1>Ask thread</h1>} />
          </Routes>
        </MemoryRouter>
      </AnnouncerProvider>
    </LocaleProvider>,
  )
}

describe('Explorer Ask popup', () => {
  it('opens conversations in a popup without leaving Explorer', async () => {
    renderExplorer()

    fireEvent.click(await screen.findByRole('button', { name: 'Ask' }))

    expect(await screen.findByRole('heading', { name: 'Order flow' }, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New conversation' })).toBeInTheDocument()
    expect(screen.getByTestId('app-location')).toHaveTextContent('/explorer')

    fireEvent.click(screen.getByRole('link', { name: 'All conversations' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Ask' })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Which table does GET /orders/{id} read?' }, { timeout: 4000 })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('link', { name: 'Back' }))

    expect(await screen.findByRole('heading', { name: 'Order flow' }, { timeout: 4000 })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('link', { name: 'All conversations' }))
    fireEvent.click(await screen.findByRole('link', { name: 'Which table does GET /orders/{id} read?' }, { timeout: 4000 }))

    expect(await screen.findByRole('heading', { name: 'Order flow' }, { timeout: 4000 })).toBeInTheDocument()
    expect(screen.getByTestId('app-location')).toHaveTextContent('/explorer')
    expect(screen.queryByRole('heading', { name: 'Ask page' })).not.toBeInTheDocument()
  }, 15000)
})

describe('Explorer structure view', () => {
  it('adds Structure beside Graph and List and keeps those view switches', async () => {
    renderExplorer()

    const viewGroup = await screen.findByRole('group', { name: 'Canvas view mode' })
    const graph = within(viewGroup).getByRole('button', { name: 'Graph' })
    const list = within(viewGroup).getByRole('button', { name: 'List' })
    const structure = within(viewGroup).getByRole('button', { name: 'Structure' })
    expect(within(viewGroup).getAllByRole('button')).toHaveLength(3)
    expect(list).toHaveAttribute('aria-pressed', 'true')
    expect(graph).toHaveAttribute('aria-pressed', 'false')
    expect(structure).toHaveAttribute('aria-pressed', 'false')
    const apiList = (await screen.findByRole('heading', { name: 'Entrypoints' })).closest('.explorer-list-fallback') as HTMLElement
    expect(await within(apiList).findByRole('button', { name: /GET \/orders\/\{id\}/ })).toBeInTheDocument()

    fireEvent.click(graph)
    expect(graph).toHaveAttribute('aria-pressed', 'true')
    expect(list).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('heading', { name: 'Pick a starting entity' })).toBeInTheDocument()
  })

  it('lays the snapshot out as one source tree and opens detail when selecting a node', async () => {
    renderExplorer()

    fireEvent.click(await screen.findByRole('button', { name: 'Structure' }))
    const tree = await screen.findByRole('tree', { name: 'Snapshot structure' })
    expect(within(tree).queryByRole('treeitem', { name: 'Module' })).not.toBeInTheDocument()
    const app = within(tree).getByRole('treeitem', { name: 'app' })
    expect(app).toHaveAttribute('aria-expanded', 'true')

    const repositories = within(tree).getByRole('treeitem', { name: 'repositories' })
    expect(repositories).toHaveAttribute('aria-expanded', 'true')
    const repoNode = repositories.closest('li')
    expect(repoNode).not.toBeNull()
    const orders = within(repoNode as HTMLElement).getByRole('treeitem', { name: 'orders' })
    expect(orders).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(within(tree).getByRole('treeitem', { name: /^load_order,/ }))
    expect(await screen.findByRole('heading', { name: 'load_order' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Structure' })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Graph' }))
    expect(screen.queryByRole('tree', { name: 'Snapshot structure' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Pick a starting entity' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'List' }))
    expect(screen.getByRole('button', { name: 'List' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Structure' })).toHaveAttribute('aria-pressed', 'false')
  }, 15000)
})

describe('Explorer project overview', () => {
  it('shows the loading canvas instead of the empty picker while overview is in flight', async () => {
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      unobserve() {}
      disconnect() {}
    })
    renderExplorer()
    fireEvent.click(await screen.findByRole('button', { name: 'Graph' }))
    fireEvent.click(screen.getByRole('button', { name: 'Project overview' }))

    expect(screen.queryByRole('heading', { name: 'Pick a starting entity' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Knowledge graph canvas')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Loading graph…' })).toBeInTheDocument()
    const canvas = await screen.findByLabelText('Knowledge graph canvas', {}, { timeout: 8000 })
    expect(within(canvas).getByText('handle_order_event')).toBeInTheDocument()
    expect(within(canvas).getByText('GET /orders/{id}')).toBeInTheDocument()
  }, 15000)

  it('replaces a selected endpoint flow with the whole snapshot, not that endpoint subgraph', async () => {
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      unobserve() {}
      disconnect() {}
    })
    const client = getRkgClient()
    const original = client.getSubgraph.bind(client)
    const calls: SubgraphParams[] = []
    client.getSubgraph = async (params) => {
      calls.push({ ...params })
      return original(params)
    }
    try {
      renderExplorer()
      const apiList = (await screen.findByRole('heading', { name: 'Entrypoints' })).closest('.explorer-list-fallback') as HTMLElement
      fireEvent.click(await within(apiList).findByRole('button', { name: /GET \/orders\/\{id\}/ }))
      const flow = await screen.findByLabelText('Knowledge graph canvas')
      expect(within(flow).queryByText('handle_order_event')).not.toBeInTheDocument()
      expect(await screen.findByRole('heading', { name: 'GET /orders/{id}' })).toBeInTheDocument()
      const scopedBefore = calls.filter(endpointScopedCall).length
      expect(scopedBefore).toBeGreaterThan(0)

      fireEvent.click(screen.getByRole('button', { name: 'Overview' }))

      expect(screen.queryByLabelText('Knowledge graph canvas')).not.toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: 'Pick a starting entity' })).not.toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Loading graph…' })).toBeInTheDocument()
      const canvas = await screen.findByLabelText('Knowledge graph canvas', {}, { timeout: 8000 })
      expect(await within(canvas).findByText('handle_order_event')).toBeInTheDocument()
      expect(within(canvas).getByText('GET /orders/{id}')).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: 'GET /orders/{id}' })).not.toBeInTheDocument()
      expect(calls.filter(endpointScopedCall)).toHaveLength(scopedBefore)
      expect(calls.some((params) =>
        params.root_id === 'ent-topic-order-events' && params.max_edges === 80,
      )).toBe(true)

      const callsAfterOverview = calls.length
      fireEvent.click(screen.getByRole('button', { name: 'Options' }))
      fireEvent.change(screen.getByLabelText('Depth'), { target: { value: '2' } })
      expect(calls).toHaveLength(callsAfterOverview)
      expect(within(canvas).getByText('handle_order_event')).toBeInTheDocument()
    } finally {
      client.getSubgraph = original
    }
  }, 15000)
})

describe('Explorer graph relationships', () => {
  it('offers optional file/folder and dependency overlays in flow view', async () => {
    renderExplorer()
    fireEvent.click(screen.getByRole('button', { name: 'Options' }))
    expect(screen.getByRole('radio', { name: 'Entity flow' })).toHaveAttribute('aria-checked', 'true')
    expect(screen.queryByLabelText('Direction')).not.toBeInTheDocument()
    const structure = screen.getByLabelText('Show files and folders')
    expect(structure).not.toBeChecked()
    fireEvent.click(structure)
    expect(structure).toBeChecked()
    expect(screen.getByLabelText('Show declared dependencies')).not.toBeChecked()
    fireEvent.click(screen.getByRole('radio', { name: 'All relationships' }))
    expect(screen.queryByLabelText('Show files and folders')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Direction')).toBeEnabled()
  })
  it('shows direct API relationships and lets the reader move to the next entity', async () => {
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      unobserve() {}
      disconnect() {}
    })
    renderExplorer()
    await screen.findAllByRole('button', { name: /GET \/orders\/\{id\}/ })
    fireEvent.change(screen.getByLabelText('Graph preset'), { target: { value: 'api_to_db' } })

    const relationships = await screen.findByText('Relationships')
    const panel = relationships.closest('.detail-relations') as HTMLElement
    expect(panel.closest('.drawer-body')).not.toBeNull()
    expect(await within(panel).findByText('GET /orders/{id}')).toBeInTheDocument()
    const handler = (await within(panel).findByText('get_order')).closest('button')
    expect(handler).not.toBeNull()
    fireEvent.click(handler as HTMLButtonElement)
    expect(await within(panel).findByText('get_order', { selector: '.graph-relations-entity' })).toBeInTheDocument()
    expect(within(panel).getByRole('button', { name: /Show all links/ })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'get_order' })).toBeInTheDocument()
  }, 15000)

  it('opens an API from the default list as a flow with the detail column', async () => {
    vi.stubGlobal('ResizeObserver', class {
      observe() {}
      unobserve() {}
      disconnect() {}
    })
    renderExplorer()
    const apiList = (await screen.findByRole('heading', { name: 'Entrypoints' })).closest('.explorer-list-fallback') as HTMLElement
    fireEvent.click(await within(apiList).findByRole('button', { name: /GET \/orders\/\{id\}/ }))

    expect(await screen.findByLabelText('Knowledge graph canvas')).toBeInTheDocument()
    expect(await screen.findByText('Relationships')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Graph' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'List' })).toHaveAttribute('aria-pressed', 'false')
    expect(await screen.findByRole('heading', { name: 'GET /orders/{id}' })).toBeInTheDocument()
  }, 15000)
})
