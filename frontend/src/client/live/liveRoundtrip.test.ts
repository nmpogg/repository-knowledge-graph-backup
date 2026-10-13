import { spawn, type ChildProcess } from 'node:child_process'
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { createLiveClient } from './liveClient'
import type { RkgClient } from '../mock/mockClient'

const TOKEN = 'live-ui-session'
const PORT = 18000 + Math.floor(Math.random() * 2000)
const repoRoot = resolve(process.cwd(), '..')

let child: ChildProcess | undefined
let root: string | undefined
let client: RkgClient

function killTree(proc: ChildProcess | undefined) {
  if (!proc?.pid) return
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(proc.pid), '/T', '/F'], { stdio: 'ignore' })
  } else {
    proc.kill()
  }
}

async function waitUntilReady(): Promise<void> {
  const deadline = Date.now() + 20_000
  let last = 'not started'
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${PORT}/api/v1/repositories`)
      if (response.ok || response.status === 401) return
      last = `HTTP ${response.status}`
    } catch (err) {
      last = err instanceof Error ? err.message : 'connect failed'
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 200))
  }
  throw new Error(`RKG API did not become ready (${last})`)
}

async function waitJob(jobId: string) {
  for (let i = 0; i < 40; i += 1) {
    const { job } = await client.getIndexJob(jobId)
    if (['succeeded', 'succeeded_with_warnings', 'failed', 'detecting'].includes(job.stage)) {
      if (job.stage !== 'detecting' || (job.report?.app_candidates?.length ?? 0) > 1) return job
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 250))
  }
  throw new Error('job did not settle')
}

describe('live API round trip', () => {
  beforeAll(async () => {
    root = mkdtempSync(join(tmpdir(), 'rkg-ui-'))
    const allowed = join(root, 'src')
    mkdirSync(allowed)
    writeFileSync(
      join(allowed, 'pyproject.toml'),
      '[project]\ndependencies = ["fastapi>=0.100"]\n',
      'utf8',
    )
    writeFileSync(
      join(allowed, 'uv.lock'),
      '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n',
      'utf8',
    )
    writeFileSync(
      join(allowed, 'app.py'),
      'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/orders/{order_id}")\ndef get_order(order_id: str):\n    return {"id": order_id}\n',
      'utf8',
    )
    const apps = join(root, 'apps')
    mkdirSync(apps)
    writeFileSync(
      join(apps, 'pyproject.toml'),
      '[project]\ndependencies = ["fastapi>=0.100"]\n',
      'utf8',
    )
    writeFileSync(
      join(apps, 'uv.lock'),
      '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n',
      'utf8',
    )
    writeFileSync(
      join(apps, 'one.py'),
      'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/one")\ndef one():\n    pass\n',
      'utf8',
    )
    writeFileSync(
      join(apps, 'two.py'),
      'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/two")\ndef two():\n    pass\n',
      'utf8',
    )
    client = createLiveClient({
      baseUrl: `http://127.0.0.1:${PORT}`,
      sessionToken: TOKEN,
    })
    const other = join(root, 'other')
    mkdirSync(other)
    writeFileSync(join(other, 'note.py'), 'def note():\n    return None\n', 'utf8')
    child = spawn(
      process.env.RKG_TEST_PYTHON ?? resolve(repoRoot, '.venv',
        process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
      [
        '-m',
        'rkg',
        '--db',
        join(root, 'graph'),
        '--allow-root',
        allowed,
        '--allow-root',
        apps,
        '--allow-root',
        other,
        'serve',
        '--port',
        String(PORT),
      ],
      {
        cwd: repoRoot,
        env: { ...process.env, RKG_SESSION_TOKEN: TOKEN },
        stdio: 'ignore',
      },
    )
    await waitUntilReady()
  }, 30_000)

  afterAll(() => {
    killTree(child)
    if (root) rmSync(root, { recursive: true, force: true })
  })

  it('registers a local repository, rejects an outside path, and opens the mapped graph', async () => {
    const created = await client.createRepository({
      display_name: 'Orders live',
      source_type: 'local',
      path: join(root ?? '', 'src'),
    })
    expect(created.active_snapshot_id).toBeNull()
    expect(created.source_locator_redacted).not.toContain(root ?? 'unused')
    const listed = await client.listRepositories({ q: 'Orders live' })
    expect(listed.page.total).toBeGreaterThan(0)

    await expect(
      client.createRepository({
        display_name: 'Outside',
        source_type: 'local',
        path: root ?? '',
      }),
    ).rejects.toMatchObject({ status: 422, code: 'source_outside_allowed_roots' })

    const started = await client.startIndexJob(created.repository_id)
    const finished = await waitJob(started.job_id)
    expect(['succeeded', 'succeeded_with_warnings']).toContain(finished.stage)
    const snapshotId = finished.snapshot_id
    expect(snapshotId).toBeTruthy()
    const found = await client.searchEntities(snapshotId ?? '', { type: 'endpoint' })
    expect(found.items.some((item) => item.type === 'endpoint')).toBe(true)
    const rootId = found.items[0]?.id ?? ''
    const graph = await client.getSubgraph({ snapshot_id: snapshotId ?? '', root_id: rootId, direction: 'outgoing', depth: 2 })
    expect(graph.nodes.some((node) => node.id === rootId)).toBe(true)
    const exported = await client.exportContext({
      snapshot_id: snapshotId ?? '',
      root_id: rootId,
      direction: 'outgoing',
      edge_types: ['handled_by', 'calls'],
      depth: 2,
      max_nodes: 20,
      max_edges: 40,
      max_chars: 8000,
    })
    expect(exported.schema_version).toBeTruthy()
    expect(exported.root_id).toBe(rootId)
  }, 60_000)

  it('surfaces multiple app candidates on the detecting stage the job screen already uses', async () => {
    const created = await client.createRepository({
      display_name: 'Two apps',
      source_type: 'local',
      path: join(root ?? '', 'apps'),
    })
    const started = await client.startIndexJob(created.repository_id)
    const job = await waitJob(started.job_id)
    expect(job.stage).toBe('detecting')
    expect(job.report?.app_candidates?.length).toBeGreaterThan(1)
    expect(job.report?.selected_app_id == null || job.report.selected_app_id === '').toBe(true)
  }, 60_000)

  it('guards update, active snapshot delete, and cross-repository snapshot reads', async () => {
    await expect(
      client.createRepository({
        display_name: 'Duplicate source',
        source_type: 'local',
        path: join(root ?? '', 'src'),
      }),
    ).rejects.toMatchObject({ status: 409, code: 'repository_conflict' })

    await expect(
      client.createRepository({
        display_name: 'Missing',
        source_type: 'local',
        path: join(root ?? '', 'src', 'does-not-exist'),
      }),
    ).rejects.toMatchObject({ status: 422, code: 'source_not_found' })

    const listed = await client.listRepositories({ q: 'Orders live' })
    const repo = listed.items[0]
    expect(repo).toBeTruthy()
    const detail = await client.getRepository(repo?.repository_id ?? '')
    const renamed = await client.updateRepository(detail.repository_id, {
      expected_revision: detail.revision,
      display_name: 'Orders renamed',
    })
    expect(renamed.revision).toBe(detail.revision + 1)
    await expect(
      client.updateRepository(detail.repository_id, {
        expected_revision: detail.revision,
        display_name: 'Stale',
      }),
    ).rejects.toMatchObject({ status: 409, code: 'repository_conflict' })

    const snapshots = await client.listSnapshots(detail.repository_id)
    const active = snapshots.items.find((item) => item.is_active)
    expect(active?.source_revision.startsWith('manifest:')).toBe(true)
    await expect(
      client.deleteSnapshot(detail.repository_id, active?.snapshot_id ?? ''),
    ).rejects.toMatchObject({ status: 409, code: 'snapshot_active' })

    const isolated = await client.createRepository({
      display_name: 'Other',
      source_type: 'local',
      path: join(root ?? '', 'other'),
    })
    await expect(
      client.getSnapshot(isolated.repository_id, active?.snapshot_id ?? ''),
    ).rejects.toMatchObject({ status: 404 })
    await client.deleteRepository(isolated.repository_id)
    await expect(client.getRepository(isolated.repository_id)).rejects.toMatchObject({ status: 404 })
  }, 30_000)
})
