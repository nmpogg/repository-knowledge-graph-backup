import { describe, expect, it } from 'vitest'
import type { EntitySummary, EntityType, Paged } from '../../types/api'
import {
  buildStructureTree,
  collectSnapshotEntities,
  defaultExpandedKeys,
  STRUCTURE_TIER2_LIMIT,
  type StructureBranch,
  type StructureNode,
} from './structureTree'

function entity(
  id: string,
  type: EntityType,
  name: string,
  qualifiedName: string,
  filePath?: string,
): EntitySummary {
  return {
    id,
    type,
    name,
    qualified_name: qualifiedName,
    ...(filePath ? { file_path: filePath } : {}),
  }
}

function branch(nodes: StructureNode[], label: string): StructureBranch {
  const found = nodes.find((node) => node.kind === 'branch' && node.label === label)
  if (!found || found.kind !== 'branch') {
    throw new Error(`missing branch ${label}`)
  }
  return found
}

function labels(nodes: StructureNode[]): string[] {
  return nodes.map((node) => node.label)
}

function walk(nodes: StructureNode[]): StructureNode[] {
  const found: StructureNode[] = []
  for (const node of nodes) {
    found.push(node)
    if (node.kind === 'branch') found.push(...walk(node.children))
  }
  return found
}

function leafIds(nodes: StructureNode[]): string[] {
  const ids: string[] = []
  for (const node of nodes) {
    if (node.kind === 'leaf') ids.push(node.entity.id)
    else ids.push(...leafIds(node.children))
  }
  return ids
}

describe('buildStructureTree', () => {
  it('uses one selectable canonical directory and file identity with package metadata', () => {
    const folder = entity('dir', 'directory', 'service', 'src/service', 'src/service')
    const file = { ...entity('java', 'file', 'User.java', 'User.java', 'src/service/User.java'),
      scope_name: 'com.example' }
    const method = entity('method', 'function', 'find', 'com.example.User.find', 'src/service/User.java')
    const init = entity('init', 'file', '__init__.py', 'src.service', 'src/service/__init__.py')
    const roots = buildStructureTree([folder, file, method, init], '2')
    const nodes = walk(roots)
    const directories = nodes.filter((node) => node.kind === 'branch' && node.entity?.id === 'dir')
    expect(directories).toHaveLength(1)
    expect(directories[0]?.label).toBe('service')
    const service = branch(branch(roots, 'src').children, 'service')
    expect(labels(service.children)).toEqual(['__init__.py', 'User.java'])
    expect(branch(service.children, 'User.java').entity?.id).toBe('java')
    expect(leafIds(service.children)).toContain('method')
    expect(buildStructureTree([init, method, file, folder], '2')).toEqual(roots)
  })

  it('keeps __init__.py as a source file in new root-only snapshots', () => {
    const roots = buildStructureTree([entity('init', 'file', '__init__.py', '__init__', '__init__.py')], '2')
    expect(labels(roots)).toEqual(['__init__.py'])
    expect(leafIds(roots)).toEqual(['init'])
  })

  it('keeps pathless dependencies separate from directories with the same name', () => {
    const roots = buildStructureTree([
      entity('dir', 'directory', 'pkg', 'pkg', 'pkg'),
      entity('unit', 'file', 'unit.py', 'pkg.unit', 'pkg/unit.py'),
      entity('dependency', 'dependency', 'pkg', 'pkg'),
    ], '2')
    expect(roots).toHaveLength(2)
    expect(new Set(roots.map((node) => node.key)).size).toBe(2)
    expect(leafIds(roots)).toEqual(['unit', 'dependency'])
    expect(branch(roots, 'pkg').entity?.id).toBe('dir')
  })
  it('cuts one tree by source directory and hangs symbols under the file', () => {
    const roots = buildStructureTree([
      entity('su-notes', 'module', 'notes.py', 'app.api.notes', 'app/api/notes.py'),
      entity('ns-notes', 'module', 'notes', 'app.api.notes', 'app/api/notes.py'),
      entity('note', 'class', 'Note', 'app.api.notes.Note', 'app/api/notes.py'),
      entity('create', 'function', 'create_note', 'app.api.notes.create_note', 'app/api/notes.py'),
      entity('routes', 'module', 'routes.py', 'app.api.routes', 'app/api/routes.py'),
      entity('ns-routes', 'module', 'routes', 'app.api.routes', 'app/api/routes.py'),
      entity('domain', 'module', 'domain', 'app.domain', 'app/domain/__init__.py'),
      entity('su-domain', 'module', '__init__.py', 'app.domain', 'app/domain/__init__.py'),
      entity('repository', 'module', 'repository', 'app.repository', 'app/repository/__init__.py'),
      entity('service', 'module', 'service', 'app.service', 'app/service/__init__.py'),
    ])

    expect(labels(roots)).toEqual(['app'])
    const app = branch(roots, 'app')
    expect(app.tier).toBe('directory')
    expect(labels(app.children)).toEqual(['api', 'domain', 'repository', 'service'])

    const api = branch(app.children, 'api')
    expect(labels(api.children)).toEqual(['notes.py', 'routes.py'])
    const notes = branch(api.children, 'notes.py')
    expect(notes.tier).toBe('file')
    expect(labels(notes.children)).toEqual(
      ['Note', 'create_note'].sort((a, b) => a.localeCompare(b)),
    )
    expect(leafIds(notes.children).sort()).toEqual(['create', 'note'])
    expect(labels(walk(roots))).not.toContain('__init__')

    const routes = api.children.find((node) => node.label === 'routes.py')
    expect(routes?.kind).toBe('leaf')
    if (routes?.kind === 'leaf') expect(routes.entity.id).toBe('routes')

    for (const name of ['domain', 'repository', 'service']) {
      const node = app.children.find((item) => item.label === name)
      expect(node?.kind).toBe('leaf')
    }
    expect(buildStructureTree([])).toEqual([])
  })

  it('keeps a source file and its module as one file node', () => {
    const roots = buildStructureTree([
      entity('su', 'file', 'notes.py', 'service.notes', 'service/notes.py'),
      entity('ns', 'module', 'notes', 'service.notes', 'service/notes.py'),
      entity('cls', 'class', 'Note', 'service.notes.Note', 'service/notes.py'),
    ])
    const file = branch(branch(roots, 'service').children, 'notes.py')
    expect(file.tier).toBe('file')
    expect(labels(file.children)).toEqual(['Note'])
    expect(file.children[0]?.kind).toBe('leaf')
    if (file.children[0]?.kind === 'leaf') expect(file.children[0].entity.type).toBe('class')
    const leaves = walk(roots).filter((node) => node.kind === 'leaf')
    expect(leaves.map((node) => (node.kind === 'leaf' ? node.entity.id : ''))).toEqual(['cls'])
    expect(leaves.map((node) => (node.kind === 'leaf' ? node.entity.type : ''))).toEqual(['class'])
  })

  it('nests a method under its class and keeps a colon as a symbol boundary', () => {
    const roots = buildStructureTree([
      entity('note', 'class', 'Note', 'app.api.notes.Note', 'app/api/notes.py'),
      entity('method', 'function', 'create', 'app.api.notes.Note.create', 'app/api/notes.py'),
      entity('route', 'endpoint', 'GET /orders/{id}', 'app.api.orders:get_order', 'app/api/orders.py'),
      entity('handler', 'function', 'get_order', 'app.api.orders:get_order', 'app/api/orders.py'),
      entity('setting', 'config', 'DATABASE_URL', 'settings:app.api.orders:DATABASE_URL', 'app/api/orders.py'),
    ])

    const notes = branch(branch(branch(roots, 'app').children, 'api').children, 'notes.py')
    const note = branch(notes.children, 'Note')
    expect(note.tier).toBe('symbol')
    expect(leafIds(note.children).sort()).toEqual(['method', 'note'])

    const orders = branch(branch(branch(roots, 'app').children, 'api').children, 'orders.py')
    expect(labels(orders.children)).toEqual(
      ['DATABASE_URL', 'get_order', 'get_order'].sort((a, b) => a.localeCompare(b)),
    )
    expect(orders.children.every((node) => !node.label.includes(':'))).toBe(true)
    expect(leafIds(orders.children).sort()).toEqual(['handler', 'route', 'setting'])
  })

  it('puts symbols from __init__.py on the package and keeps pathless roots beside it', () => {
    const roots = buildStructureTree([
      entity('pkg', 'module', 'api', 'app.api', 'app/api/__init__.py'),
      entity('app-cls', 'class', 'App', 'app.api.App', 'app\\api\\__init__.py'),
      entity('notes', 'module', 'notes.py', 'app.api.notes', 'app/api/notes.py'),
      entity('orders', 'table', 'orders', 'db.tables:orders'),
      entity('events', 'topic', 'order.events', 'kafka.topics:order.events'),
      entity('httpx', 'dependency', 'httpx', 'httpx'),
    ])

    const app = branch(roots, 'app')
    const api = branch(app.children, 'api')
    expect(labels(api.children)).toEqual(['App', 'notes.py'].sort((a, b) => a.localeCompare(b)))
    expect(labels(roots)).toEqual(['app', 'db', 'httpx', 'kafka'])
    expect(branch(roots, 'db').tier).toBe('directory')
    const tables = branch(branch(roots, 'db').children, 'tables')
    expect(leafIds(tables.children)).toEqual(['orders'])
    expect(labels(roots).includes('Table')).toBe(false)
    expect(labels(roots).includes('Topic')).toBe(false)
  })

  it('keeps the same symbol name apart when the files differ', () => {
    const roots = buildStructureTree([
      entity('a', 'function', 'run', 'pkg.alpha.run', 'pkg/alpha.py'),
      entity('b', 'function', 'run', 'pkg.beta.run', 'pkg/beta.py'),
    ])
    const alpha = branch(branch(roots, 'pkg').children, 'alpha.py')
    const beta = branch(branch(roots, 'pkg').children, 'beta.py')
    expect(leafIds(alpha.children)).toEqual(['a'])
    expect(leafIds(beta.children)).toEqual(['b'])
  })

  it('uses name when qualified_name is blank', () => {
    const roots = buildStructureTree([
      entity('left', 'class', 'Left', ''),
      entity('right', 'class', 'Right', '   '),
    ])
    expect(labels(roots)).toEqual(['Left', 'Right'])
    expect(roots.every((node) => node.kind === 'leaf')).toBe(true)
  })

  it('opens the root and the next directory tier, and leaves files closed', () => {
    const roots = buildStructureTree([
      entity('note', 'class', 'Note', 'app.api.notes.Note', 'app/api/notes.py'),
      entity('orders', 'table', 'orders', 'db.tables:orders'),
    ])
    const open = defaultExpandedKeys(roots)
    const app = branch(roots, 'app')
    const api = branch(app.children, 'api')
    const notes = branch(api.children, 'notes.py')
    const db = branch(roots, 'db')
    const tables = branch(db.children, 'tables')
    expect(open).toEqual([app.key, api.key, db.key, tables.key])
    expect(open).not.toContain(notes.key)
    expect(notes.tier).toBe('file')
  })

  it('hides tier 3 when one root has more than 10 tier-2 nodes', () => {
    const wide = Array.from({ length: STRUCTURE_TIER2_LIMIT + 1 }, (_, index) =>
      entity(`fn-${index}`, 'function', `run${index}`, `app.m${index}.mod.run`, `app/m${index}/mod.py`),
    )
    const roots = buildStructureTree(wide)
    const open = defaultExpandedKeys(roots)
    const app = branch(roots, 'app')
    const tier2 = branch(app.children, 'm0')
    expect(app.children).toHaveLength(STRUCTURE_TIER2_LIMIT + 1)
    expect(open).toEqual([app.key])
    expect(open).not.toContain(tier2.key)
  })

  it('still opens tier 3 when a root has 10 tier-2 nodes', () => {
    const fitted = Array.from({ length: STRUCTURE_TIER2_LIMIT }, (_, index) =>
      entity(`fn-${index}`, 'function', `run${index}`, `app.m${index}.mod.run`, `app/m${index}/mod.py`),
    )
    const roots = buildStructureTree(fitted)
    const open = defaultExpandedKeys(roots)
    const app = branch(roots, 'app')
    const tier2 = branch(app.children, 'm0')
    expect(open).toContain(app.key)
    expect(open).toContain(tier2.key)
  })
})

describe('collectSnapshotEntities', () => {
  it('follows pages until the snapshot total is reached', async () => {
    const calls: number[] = []
    const all = [
      entity('1', 'module', 'a', 'a'),
      entity('2', 'module', 'b', 'b'),
      entity('3', 'module', 'c', 'c'),
    ]
    const search = async (params: {
      offset: number
      limit: number
    }): Promise<Paged<EntitySummary>> => {
      calls.push(params.offset)
      return {
        items: all.slice(params.offset, params.offset + params.limit),
        page: { offset: params.offset, limit: params.limit, total: all.length },
      }
    }

    const items = await collectSnapshotEntities(search, 2)
    expect(calls).toEqual([0, 2])
    expect(items.map((item) => item.id)).toEqual(['1', '2', '3'])
  })

  it('returns no rows when the snapshot has no entities', async () => {
    const items = await collectSnapshotEntities(async () => ({
      items: [],
      page: { offset: 0, limit: 100, total: 0 },
    }))
    expect(items).toEqual([])
  })
})
