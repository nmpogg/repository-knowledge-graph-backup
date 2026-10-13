import { describe, expect, it, vi } from 'vitest'
import { createLiveClient } from './liveClient'

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

describe('live RkgClient', () => {
  it('rejects a backend that silently ignores the requested flow view', async () => {
    const client = createLiveClient({ fetchImpl: vi.fn(async () => jsonResponse({ nodes: [], edges: [] })) })
    await expect(client.getSubgraph({ snapshot_id: 'snap', root_id: 'root', view: 'flow' }))
      .rejects.toMatchObject({ code: 'graph_flow_unavailable' })
  })
  it('sends flow and optional context controls to the backend', async () => {
    const fetchImpl = vi.fn(async (_url: string) => jsonResponse({
      snapshot_id: 'snap', root_id: 'root', view: 'flow', nodes: [], edges: [], truncated: false,
      truncation_reasons: [], limits: { depth: 6, max_nodes: 50, max_edges: 100 },
    }))
    const client = createLiveClient({ fetchImpl })
    await client.getSubgraph({ snapshot_id: 'snap', root_id: 'root', view: 'flow',
      include_structure: true, include_dependencies: false, depth: 6 })
    const url = new URL(String(fetchImpl.mock.calls[0][0]), 'http://127.0.0.1')
    expect(url.searchParams.get('view')).toBe('flow')
    expect(url.searchParams.get('include_structure')).toBe('true')
    expect(url.searchParams.get('include_dependencies')).toBe('false')
  })
  it('sends the session header and adapts repository list', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({
        items: [
          {
            repository_id: 'repo-1',
            revision: 1,
            display_name: 'Orders',
            source_type: 'local',
            source_locator_redacted: 'local:orders',
            active_snapshot_id: null,
            created_at: 't',
            updated_at: 't',
          },
        ],
        total: 1,
        offset: 0,
        limit: 20,
      }),
    )
    const client = createLiveClient({
      baseUrl: 'http://127.0.0.1:8000',
      sessionToken: 'local-session',
      fetchImpl,
    })
    const page = await client.listRepositories()
    expect(page.page.total).toBe(1)
    expect(page.items[0]?.display_name).toBe('Orders')
    const [, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit]
    expect(new Headers(init.headers).get('X-RKG-Session')).toBe('local-session')
  })

  it('keeps source_outside_allowed_roots instead of collapsing it', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ error: { code: 'source_outside_allowed_roots', message: 'source outside allowed roots' } }, 422),
    )
    const client = createLiveClient({ sessionToken: 'local-session', fetchImpl })
    await expect(
      client.createRepository({ display_name: 'X', source_type: 'local', path: 'elsewhere' }),
    ).rejects.toMatchObject({ status: 422, code: 'source_outside_allowed_roots' })
  })

  it('asks the API for the domain type and skips interface', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ items: [], total: 0, offset: 0, limit: 20 }))
    const client = createLiveClient({ fetchImpl })
    await client.searchEntities('snap-1', { type: 'endpoint' })
    const [url] = fetchImpl.mock.calls[0] as unknown as [string]
    expect(url).toContain('type=Endpoint')
    fetchImpl.mockClear()
    await client.searchEntities('snap-1', { type: 'file' })
    const [fileUrl] = fetchImpl.mock.calls[0] as unknown as [string]
    expect(fileUrl).toContain('type=SourceUnit')
    expect(fileUrl).not.toContain('type=Namespace')
    fetchImpl.mockClear()
    await client.searchEntities('snap-1', { type: 'module' })
    const [moduleUrl] = fetchImpl.mock.calls[0] as unknown as [string]
    expect(moduleUrl).toContain('type=Namespace')
    expect(moduleUrl).not.toContain('type=SourceUnit')
    fetchImpl.mockClear()
    const empty = await client.searchEntities('snap-1', { type: 'interface' })
    expect(empty.items).toEqual([])
    expect(fetchImpl).not.toHaveBeenCalled()
  })

  it('reads Retry-After and treats an empty delete as success', async () => {
    const fetchImpl = vi.fn(async (url: string) => {
      if (String(url).includes('/index-jobs/')) {
        return jsonResponse(
          {
            job_id: 'job-1',
            repository_id: 'repo-1',
            stage: 'scanning',
            progress_revision: 1,
            report: null,
            snapshot_id: null,
            error: null,
            updated_at: 't',
          },
          200,
          { 'Retry-After': '1' },
        )
      }
      return new Response(null, { status: 204 })
    })
    const client = createLiveClient({ sessionToken: 'local-session', fetchImpl })
    const polled = await client.getIndexJob('job-1')
    expect(polled.job.stage).toBe('detecting')
    expect(polled.retryAfter).toBe(1)
    await expect(client.deleteRepository('repo-1')).resolves.toBeUndefined()
  })
})
