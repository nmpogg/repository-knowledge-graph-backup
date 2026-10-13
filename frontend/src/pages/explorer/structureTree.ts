import type { EntitySummary, Paged } from '../../types/api'

export interface StructureLeaf {
  kind: 'leaf'
  key: string
  /** Last path or symbol segment, or `name` when the qualified name is empty. */
  label: string
  entity: EntitySummary
}

export interface StructureBranch {
  kind: 'branch'
  key: string
  label: string
  /** Directory tiers open by default. File and symbol tiers stay closed. */
  tier: 'directory' | 'file' | 'symbol'
  children: StructureNode[]
  /** Canonical API identity, when this branch is a directory or source file. */
  entity?: EntitySummary
}

export type StructureNode = StructureLeaf | StructureBranch

const PAGE_SIZE = 100

interface SymbolBucket {
  children: Map<string, SymbolBucket>
  leaves: EntitySummary[]
}

interface FileBucket {
  symbols: SymbolBucket
  identities: EntitySummary[]
}

interface DirBucket {
  dirs: Map<string, DirBucket>
  files: Map<string, FileBucket>
  symbols: SymbolBucket
  identities: EntitySummary[]
}

function emptyBucket(): SymbolBucket {
  return { children: new Map(), leaves: [] }
}

function emptyFile(): FileBucket {
  return { symbols: emptyBucket(), identities: [] }
}

function emptyDir(): DirBucket {
  return { dirs: new Map(), files: new Map(), symbols: emptyBucket(), identities: [] }
}

function compareEntities(a: EntitySummary, b: EntitySummary): number {
  const byName = a.name.localeCompare(b.name)
  if (byName !== 0) return byName
  return a.id.localeCompare(b.id)
}

function compareNodes(a: StructureNode, b: StructureNode): number {
  const byLabel = a.label.localeCompare(b.label)
  if (byLabel !== 0) return byLabel
  return a.key.localeCompare(b.key)
}

function fallbackLabel(entity: EntitySummary): string {
  return entity.name.trim() || entity.qualified_name.trim() || entity.id
}

/** `\` becomes `/`. Leading slashes are dropped. */
function normalizePath(filePath: string): string {
  return filePath.trim().replace(/\\/g, '/').replace(/^\/+/, '')
}

/**
 * Module qualified name of a source file, matching the indexer:
 * drop the suffix, and drop a trailing `__init__` segment.
 */
function moduleNameFromFile(filePath: string): string {
  const parts = normalizePath(filePath).split('/').filter((part) => part.length > 0)
  if (parts.length === 0) return ''
  const last = parts[parts.length - 1] ?? ''
  const dot = last.lastIndexOf('.')
  parts[parts.length - 1] = dot > 0 ? last.slice(0, dot) : last
  if (parts.length > 1 && parts[parts.length - 1] === '__init__') parts.pop()
  return parts.join('.')
}

/** Keep __init__.py as a file; only legacy snapshots collapse package files. */
function pathParts(filePath: string, canonical = false): { dirs: string[]; file: string | null } {
  const parts = normalizePath(filePath).split('/').filter((part) => part.length > 0)
  if (parts.length === 0) return { dirs: [], file: null }
  const last = parts[parts.length - 1] ?? ''
  if (!canonical && last === '__init__.py') {
    parts.pop()
    return { dirs: parts, file: null }
  }
  const file = parts.pop() ?? null
  return { dirs: parts, file }
}

function splitSymbol(value: string): string[] {
  return value
    .split(/[.:]/)
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
}

/**
 * Symbol path under a file. `:` is a symbol boundary, never a directory.
 * Empty means this entity is the file identity (SourceUnit or Namespace).
 * A qualified name that is not rooted at this file stays one leaf on the file.
 */
function symbolTail(entity: EntitySummary, moduleName: string): string[] {
  const qualified = entity.qualified_name.trim()
  if (!qualified) return []
  if (!moduleName) return [fallbackLabel(entity)]
  if (qualified === moduleName) return []
  if (qualified.startsWith(`${moduleName}.`) || qualified.startsWith(`${moduleName}:`)) {
    return splitSymbol(qualified.slice(moduleName.length + 1))
  }
  return [fallbackLabel(entity)]
}

function pushSymbol(bucket: SymbolBucket, parts: string[], entity: EntitySummary) {
  let cursor = bucket
  for (let index = 0; index < parts.length; index += 1) {
    const part = parts[index]
    if (!part) continue
    let next = cursor.children.get(part)
    if (!next) {
      next = emptyBucket()
      cursor.children.set(part, next)
    }
    cursor = next
    if (index === parts.length - 1) cursor.leaves.push(entity)
  }
}

/** SourceUnit (`file`) and Namespace (`module`) of the same file share one node. */
function isFileIdentity(entity: EntitySummary, tail: string[]): boolean {
  return entity.type === 'file' || (entity.type === 'module' && tail.length === 0)
}

function attachToFile(file: FileBucket, entity: EntitySummary, moduleName: string) {
  const tail = symbolTail(entity, moduleName)
  if (isFileIdentity(entity, tail)) {
    file.identities.push(entity)
    return
  }
  pushSymbol(file.symbols, tail.length > 0 ? tail : [fallbackLabel(entity)], entity)
}

function attachToDir(dir: DirBucket, entity: EntitySummary, moduleName: string) {
  const tail = symbolTail(entity, moduleName)
  if (isFileIdentity(entity, tail)) {
    dir.identities.push(entity)
    return
  }
  pushSymbol(dir.symbols, tail.length > 0 ? tail : [fallbackLabel(entity)], entity)
}

function placePathless(root: DirBucket, entity: EntitySummary) {
  const qualified = entity.qualified_name.trim()
  const source = qualified.length > 0 ? qualified : fallbackLabel(entity)
  const colon = source.indexOf(':')
  const dirParts =
    colon >= 0
      ? source
          .slice(0, colon)
          .split('.')
          .map((part) => part.trim())
          .filter((part) => part.length > 0)
      : source
          .split('.')
          .map((part) => part.trim())
          .filter((part) => part.length > 0)
  const symParts = colon >= 0 ? splitSymbol(source.slice(colon + 1)) : []
  const segments = dirParts.length > 0 ? dirParts : [fallbackLabel(entity)]
  let cursor = root
  for (const part of segments) {
    let next = cursor.dirs.get(part)
    if (!next) {
      next = emptyDir()
      cursor.dirs.set(part, next)
    }
    cursor = next
  }
  if (symParts.length === 0) {
    cursor.identities.push(entity)
    return
  }
  pushSymbol(cursor.symbols, symParts, entity)
}

function ensureDir(root: DirBucket, dirs: string[]): DirBucket {
  let cursor = root
  for (const part of dirs) {
    let next = cursor.dirs.get(part)
    if (!next) {
      next = emptyDir()
      cursor.dirs.set(part, next)
    }
    cursor = next
  }
  return cursor
}

/** Prefer the module whose name is the file or package label. One node only. */
function moduleRepresentative(entities: EntitySummary[], label: string): EntitySummary | null {
  const named = entities.find((entity) => entity.name === label)
  return named ?? entities[0] ?? null
}

function leafOf(label: string, entity: EntitySummary): StructureLeaf {
  return { kind: 'leaf', key: `leaf/${entity.id}`, label, entity }
}

function symbolNodes(prefix: string, bucket: SymbolBucket): StructureNode[] {
  const labels = [...bucket.children.keys()].sort((a, b) => a.localeCompare(b))
  const nodes: StructureNode[] = []
  for (const label of labels) {
    const child = bucket.children.get(label)
    if (!child) continue
    const path = `${prefix}/${label}`
    const deeper = symbolNodes(path, child)
    const leaves = [...child.leaves].sort(compareEntities).map((entity) => leafOf(label, entity))
    if (deeper.length === 0) {
      nodes.push(...leaves)
      continue
    }
    nodes.push({
      kind: 'branch',
      tier: 'symbol',
      key: path,
      label,
      children: [...leaves, ...deeper].sort(compareNodes),
    })
  }
  return nodes
}

function fileNode(pathKey: string, label: string, file: FileBucket): StructureNode | null {
  const children = symbolNodes(`file:${pathKey}`, file.symbols)
  if (children.length === 0) {
    const identity = moduleRepresentative(file.identities, label)
    if (!identity) return null
    return leafOf(label, identity)
  }
  return {
    kind: 'branch',
    tier: 'file',
    key: `file:${pathKey}`,
    label,
    children,
    entity: moduleRepresentative(file.identities, label) ?? undefined,
  }
}

function dirNode(path: string[], dir: DirBucket): StructureNode {
  const label = path[path.length - 1] ?? ''
  const children = childNodes(path, dir)
  if (children.length === 0) {
    const identity = moduleRepresentative(dir.identities, label)
    if (identity) return leafOf(label, identity)
  }
  return {
    kind: 'branch',
    tier: 'directory',
    key: `dir:${path.join('/')}`,
    label,
    children,
    entity: dir.identities.find((entity) => entity.type === 'directory'),
  }
}

function childNodes(path: string[], dir: DirBucket): StructureNode[] {
  const nodes: StructureNode[] = []
  for (const [label, child] of dir.dirs) {
    nodes.push(dirNode([...path, label], child))
  }
  for (const [label, file] of dir.files) {
    const pathKey = [...path, label].join('/')
    const node = fileNode(pathKey, label, file)
    if (node) nodes.push(node)
  }
  nodes.push(...symbolNodes(`dir:${path.join('/')}`, dir.symbols))
  nodes.sort(compareNodes)
  return nodes
}

export function buildStructureTree(entities: EntitySummary[], schemaVersion?: string): StructureNode[] {
  const root = emptyDir()
  const pathlessRoot = emptyDir()
  const canonical = schemaVersion === '2' || entities.some(
    (entity) => entity.type === 'directory' || entity.scope_name !== undefined,
  )
  const scopes = new Map(entities.filter((entity) => entity.type === 'file' && entity.file_path)
    .map((entity) => [normalizePath(entity.file_path!), entity.scope_name ?? entity.qualified_name]))
  for (const entity of entities) {
    const filePath = entity.file_path?.trim() ?? ''
    if (!normalizePath(filePath)) {
      placePathless(pathlessRoot, entity)
      continue
    }
    if (entity.type === 'directory') {
      ensureDir(root, normalizePath(filePath).split('/').filter(Boolean)).identities.push(entity)
      continue
    }
    const moduleName = scopes.get(normalizePath(filePath)) ?? moduleNameFromFile(filePath)
    const { dirs, file } = pathParts(filePath, canonical)
    const dir = ensureDir(root, dirs)
    if (!file) {
      attachToDir(dir, entity, moduleName)
      continue
    }
    let slot = dir.files.get(file)
    if (!slot) {
      slot = emptyFile()
      dir.files.set(file, slot)
    }
    attachToFile(slot, entity, moduleName)
  }
  const pathlessKeys = (node: StructureNode): StructureNode => node.kind === 'branch'
    ? { ...node, key: `pathless:${node.key}`, children: node.children.map(pathlessKeys) }
    : { ...node, key: `pathless:${node.key}` }
  return [...childNodes([], root), ...childNodes([], pathlessRoot).map(pathlessKeys)].sort(compareNodes)
}

/**
 * Root is tier 1. A root with more tier-2 nodes than this shows only tier 2.
 */
export const STRUCTURE_TIER2_LIMIT = 10

/**
 * Tiers 1 and 2 start open, and tier 3 opens with them.
 * When one root has more than 10 nodes at tier 2, that root stops at tier 2.
 * Files stay closed.
 */
export function defaultExpandedKeys(nodes: StructureNode[]): string[] {
  const keys: string[] = []
  const visit = (nodeList: StructureNode[], depth: number, hideTier3: boolean) => {
    for (const node of nodeList) {
      if (node.kind !== 'branch' || node.tier !== 'directory') continue
      if (depth >= 1 && hideTier3) continue
      if (depth >= 3) continue
      keys.push(node.key)
      const nextHide = depth === 0 ? node.children.length > STRUCTURE_TIER2_LIMIT : hideTier3
      visit(node.children, depth + 1, nextHide)
    }
  }
  visit(nodes, 0, false)
  return keys
}

/**
 * Follow `GET /api/v1/entities` pages until the snapshot is exhausted.
 * Callers must not pass a query or type filter.
 */
export async function collectSnapshotEntities(
  search: (params: { offset: number; limit: number }) => Promise<Paged<EntitySummary>>,
  pageSize = PAGE_SIZE,
): Promise<EntitySummary[]> {
  const items: EntitySummary[] = []
  let offset = 0
  let total = Number.POSITIVE_INFINITY
  const seenOffsets = new Set<number>()
  while (offset < total) {
    if (seenOffsets.has(offset)) break
    seenOffsets.add(offset)
    const page = await search({ offset, limit: pageSize })
    if (page.items.length === 0) break
    items.push(...page.items)
    const reported = page.page.total
    if (!Number.isFinite(reported) || reported < 0) break
    total = reported
    offset += page.items.length
    if (page.items.length < pageSize) break
  }
  return items
}
