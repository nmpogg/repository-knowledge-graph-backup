import { describe, expect, it } from 'vitest'
import { createMockClient } from './mock/mockClient'
import { DEMO_REPO_ID, DEMO_SNAPSHOT_ID } from './mock/fixtures'
import { RkgApiError } from '../types/api'

async function waitForJob(
  client: ReturnType<typeof createMockClient>,
  jobId: string,
  maxPolls = 12,
) {
  for (let i = 0; i < maxPolls; i += 1) {
    const { job } = await client.getIndexJob(jobId)
    if (['succeeded', 'succeeded_with_warnings', 'failed'].includes(job.stage)) {
      return job
    }
  }
  throw new Error('job did not reach terminal stage')
}

describe('mock RkgClient', () => {
  it('lists seeded repositories newest-first', async () => {
    const client = createMockClient()
    const page = await client.listRepositories()
    expect(page.page.total).toBeGreaterThan(0)
    expect(page.items[0]?.repository_id).toBe(DEMO_REPO_ID)
  })

  it('rejects paths outside allowlist without creating a repo', async () => {
    const client = createMockClient()
    const before = await client.listRepositories()
    await expect(
      client.createRepository({
        display_name: 'Bad',
        source_type: 'local',
        path: 'outside/allowed',
      }),
    ).rejects.toMatchObject({ code: 'invalid_input', status: 422 })
    const after = await client.listRepositories()
    expect(after.page.total).toBe(before.page.total)
  })

  it('returns subgraph and technologies for demo snapshot', async () => {
    const client = createMockClient()
    const graph = await client.getSubgraph({
      snapshot_id: DEMO_SNAPSHOT_ID,
      root_id: 'ent-endpoint-get-order',
      direction: 'outgoing',
      edge_types: ['handled_by', 'calls', 'depends_on', 'reads', 'writes'],
      depth: 4,
      max_nodes: 50,
    })
    expect(graph.nodes.length).toBeGreaterThan(1)
    expect(graph.edges.some((e) => e.type === 'handled_by')).toBe(true)

    const tech = await client.listTechnologies(DEMO_SNAPSHOT_ID)
    expect(tech.some((t) => t.support_state === 'supported_patterns')).toBe(true)
    expect(tech.some((t) => t.support_state === 'detected_only')).toBe(true)
  })

  it('exports context JSON with schema_version', async () => {
    const client = createMockClient()
    const ctx = await client.exportContext({
      snapshot_id: DEMO_SNAPSHOT_ID,
      root_id: 'ent-endpoint-get-order',
      direction: 'outgoing',
      edge_types: ['handled_by', 'calls', 'depends_on', 'reads', 'writes'],
      depth: 4,
      max_nodes: 50,
      max_edges: 100,
      max_chars: 20000,
    })
    expect(ctx.schema_version).toBe('context-1')
    expect(ctx.root_id).toBe('ent-endpoint-get-order')
  })

  it('patches repository with expected_revision and conflicts on stale revision', async () => {
    const client = createMockClient()
    const before = await client.getRepository(DEMO_REPO_ID)
    const updated = await client.updateRepository(DEMO_REPO_ID, {
      expected_revision: before.revision,
      display_name: 'Orders API (renamed)',
    })
    expect(updated.display_name).toBe('Orders API (renamed)')
    expect(updated.revision).toBe(before.revision + 1)
    expect(updated.source_locator_redacted).toBe(before.source_locator_redacted)

    await expect(
      client.updateRepository(DEMO_REPO_ID, {
        expected_revision: before.revision,
        display_name: 'Stale',
      }),
    ).rejects.toMatchObject({ code: 'repository_conflict', status: 409 })
  })

  it('blocks delete of active and in-use snapshots', async () => {
    const client = createMockClient()
    await expect(
      client.deleteSnapshot(DEMO_REPO_ID, DEMO_SNAPSHOT_ID),
    ).rejects.toMatchObject({ code: 'snapshot_active', status: 409 })

    await expect(
      client.deleteSnapshot(DEMO_REPO_ID, 'snap-orders-000'),
    ).rejects.toMatchObject({ code: 'snapshot_in_use', status: 409 })
  })

  it('blocks delete of repository that still has conversation refs', async () => {
    const client = createMockClient()
    await expect(client.deleteRepository(DEMO_REPO_ID)).rejects.toMatchObject({
      code: 'repository_in_use',
      status: 409,
    })
  })

  it('create → index → activate → Explorer handoff and eligible deletes', async () => {
    const client = createMockClient()
    const repo = await client.createRepository({
      display_name: 'Smoke Service',
      source_type: 'local',
      path: 'projects/smoke-service',
      app_module: 'app.main',
      app_symbol: 'app',
    })
    expect(repo.active_snapshot_id).toBeNull()
    expect(repo.revision).toBe(1)

    const job1 = await client.startIndexJob(repo.repository_id)
    expect(job1.repository_id).toBe(repo.repository_id)
    const done1 = await waitForJob(client, job1.job_id)
    expect(done1.stage).toBe('succeeded')
    expect(done1.snapshot_id).toBeTruthy()

    let current = await client.getRepository(repo.repository_id)
    expect(current.active_snapshot_id).toBe(done1.snapshot_id)

    const job2 = await client.startIndexJob(repo.repository_id)
    const done2 = await waitForJob(client, job2.job_id)
    expect(done2.snapshot_id).toBeTruthy()
    expect(done2.snapshot_id).not.toBe(done1.snapshot_id)

    current = await client.getRepository(repo.repository_id)
    expect(current.active_snapshot_id).toBe(done2.snapshot_id)

    const snaps = await client.listSnapshots(repo.repository_id)
    expect(snaps.items[0]?.snapshot_id).toBe(done2.snapshot_id)
    expect(snaps.items.length).toBeGreaterThanOrEqual(2)

    const activated = await client.activateSnapshot(
      repo.repository_id,
      done1.snapshot_id!,
    )
    expect(activated.active_snapshot_id).toBe(done1.snapshot_id)
    // Explorer handoff contract: navigate with activated snapshot id
    expect(`/explorer?snapshot_id=${activated.active_snapshot_id}`).toContain(
      done1.snapshot_id!,
    )

    await client.deleteSnapshot(repo.repository_id, done2.snapshot_id!)
    const afterDelete = await client.listSnapshots(repo.repository_id)
    expect(
      afterDelete.items.find((s) => s.snapshot_id === done2.snapshot_id),
    ).toBeUndefined()
    expect(afterDelete.items.find((s) => s.snapshot_id === done1.snapshot_id)).toBeTruthy()

    // Fresh repo without conversation refs can be deleted (cascade)
    await client.deleteRepository(repo.repository_id)
    await expect(client.getRepository(repo.repository_id)).rejects.toBeInstanceOf(
      RkgApiError,
    )
  })

  it('does not disclose foreign ownership on snapshot mismatch', async () => {
    const client = createMockClient()
    await expect(
      client.getSnapshot('repo-other', DEMO_SNAPSHOT_ID),
    ).rejects.toMatchObject({ code: 'generic_not_found', status: 404 })
  })
})
