import { describe, expect, it } from 'vitest'
import {
  domainEntityType,
  mapContext,
  mapDependency,
  mapJob,
  mapEntityDetail,
  mapPage,
  mapSubgraph,
  safeMessage,
  safePath,
  uiEntityType,
} from './mapWire'

describe('live wire mapping', () => {
  it('maps domain entity types onto UI kinds', () => {
    expect(uiEntityType('Directory')).toBe('directory')
    expect(domainEntityType('directory')).toBe('Directory')
    expect(uiEntityType('Endpoint')).toBe('endpoint')
    expect(uiEntityType('Callable')).toBe('function')
    expect(uiEntityType('SourceUnit')).toBe('file')
    expect(uiEntityType('Namespace')).toBe('module')
    expect(uiEntityType('Type')).toBe('class')
    expect(uiEntityType('DataResource')).toBe('table')
    expect(uiEntityType('ExternalDependency')).toBe('dependency')
    expect(domainEntityType('function')).toBe('Callable')
    expect(domainEntityType('file')).toBe('SourceUnit')
    expect(domainEntityType('module')).toBe('Namespace')
    expect(domainEntityType('interface')).toBeUndefined()
  })

  it('preserves module metadata and distinguishes filesystem evidence from source lines', () => {
    const detail = mapEntityDetail({ id: 'dir', type: 'Directory', name: 'pkg',
      qualified_name: 'pkg', file_path: 'pkg', evidence: [{ file_path: 'pkg/empty.py',
        start_line: 1, end_line: 1, rule: 'RKG.structure.contains.v1' }] })
    expect(detail.type).toBe('directory')
    expect(detail.evidence[0]?.provenance).toBe('filesystem')
    const file = mapEntityDetail({ id: 'file', type: 'SourceUnit', name: 'empty.py',
      qualified_name: 'pkg.empty', file_path: 'pkg/empty.py', attributes: { module_name: 'pkg.empty' } })
    expect(file.scope_name).toBe('pkg.empty')
  })

  it('maps entity definition start_line from the wire payload', () => {
    const detail = mapEntityDetail({
      id: 'fn',
      type: 'Callable',
      name: 'access_token',
      qualified_name: 'app.core.security.access_token',
      file_path: 'app/core/security.py',
      start_line: 42,
      end_line: 58,
      evidence: [
        {
          file_path: 'app/core/security.py',
          start_line: 1,
          end_line: 1,
          rule: 'RKG.structure.contains.v1',
        },
      ],
    })
    expect(detail.start_line).toBe(42)
    expect(detail.end_line).toBe(58)
    expect(detail.file_path).toBe('app/core/security.py')
  })

  it('wraps the flat page envelope the API returns', () => {
    const page = mapPage({ items: [{ repository_id: 'r1' }], total: 3, offset: 0, limit: 20 }, (item) => item)
    expect(page.page).toEqual({ total: 3, offset: 0, limit: 20 })
    expect(page.items).toHaveLength(1)
  })

  it('folds index stages into the UI stepper and pauses for app selection', () => {
    const scanning = mapJob(
      { job_id: 'j', repository_id: 'r', stage: 'extracting', progress_revision: 2, updated_at: 't' },
      '1',
    )
    expect(scanning.job.stage).toBe('indexing')
    expect(scanning.retryAfter).toBe(1)

    const choosing = mapJob(
      {
        job_id: 'j',
        repository_id: 'r',
        stage: 'failed',
        status: 'failed',
        error: { code: 'app_selection_required', message: 'app selection required' },
        report: { application_candidates: ['app.main:app', 'app.api:api'], error_code: 'app_selection_required' },
        updated_at: 't',
      },
      null,
    )
    expect(choosing.job.stage).toBe('detecting')
    expect(choosing.job.error).toBeNull()
    expect(choosing.job.report?.app_candidates?.[0]?.candidate_id).toBe('app.main:app')
    expect(choosing.retryAfter).toBe(5)
  })

  it('renames graph endpoints and hides absolute paths', () => {
    const graph = mapSubgraph({
      snapshot_id: 's',
      root_id: 'e1',
      nodes: [{ id: 'e1', type: 'Endpoint', name: 'get_order', qualified_name: 'app:get_order' }],
      edges: [{ id: 'ed', type: 'handled_by', source_id: 'e1', target_id: 'c1', rule: 'route' }],
      truncated: false,
      truncation_reasons: [],
      limits: { depth: 4, max_nodes: 50, max_edges: 100 },
    })
    expect(graph.nodes[0]?.type).toBe('endpoint')
    expect(graph.nodes[0]?.label).toBe('get_order')
    expect(graph.edges[0]).toMatchObject({ source: 'e1', target: 'c1', type: 'handled_by', label: 'handled_by' })
    expect(safePath('C:\\Users\\dev\\svc\\app.py')).toBe('svc/app.py')
  })

  it('maps dependency provenance and context diagnostics without dropping the enum', () => {
    expect(mapDependency({ id: 'd', name: 'fastapi', provenance: { status: 'declared' }, subtype: '' }).provenance).toBe('declared')
    expect(mapDependency({ id: 'd', name: 'httpx', subtype: 'imported' }).subtype).toBe('imported')
    const ctx = mapContext({
      schema_version: '1',
      repository_id: 'r',
      snapshot_id: 's',
      root_id: 'e1',
      nodes: [],
      edges: [],
      diagnostic_summary: { unresolved_import: 2 },
      truncated: false,
      truncation_reasons: [],
    })
    expect(ctx.diagnostic_summary).toEqual(['unresolved_import: 2'])
  })

  it('keeps distinct source error codes and drops host paths from messages', () => {
    expect(safeMessage('source_outside_allowed_roots', 'source outside allowed roots')).toMatch(/vùng/)
    expect(safeMessage('custom', 'see C:\\secret\\file')).toBe('Yêu cầu không hợp lệ.')
  })
})
