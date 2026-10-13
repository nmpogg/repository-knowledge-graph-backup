import type { GraphEdge, GraphNode } from '../../types/api'
import type { RkgFlowNode } from './RkgEntityNode'
import { flowLevels } from './flowPresentation'

const FLOW_ROW = 132
const FLOW_COL = 244
const WING_X = 280
const ARCH_COL = 228
const ARCH_ROW = 112
const ARCH_PER_ROW = 6
const ARCH_LAYER_GAP = 84

/** Semantic band inside a topological layer so mixed kinds stack like a flow diagram. */
const TYPE_RANK: Record<string, number> = {
  directory: 0,
  module: 1,
  file: 2,
  endpoint: 3,
  interface: 4,
  class: 5,
  function: 6,
  topic: 7,
  table: 8,
  config: 9,
  dependency: 10,
}

/** Opposing participant roles around a shared hub (left wing, right wing). */
const OPPOSING_ROLES: ReadonlyArray<readonly [string, string]> = [
  ['publishes', 'consumes'],
]

const FAN_IN_TYPES = new Set(['depends_on', 'implements', 'inherits_from'])

type Point = { x: number; y: number }
type RoleWing = 'reads' | 'writes' | 'depends' | 'main'

export type FlowLayoutKind = 'hub_opposing' | 'fan_in' | 'pipeline' | 'layered'

export type FlowLayoutClassification =
  | {
      kind: 'hub_opposing'
      hubId: string
      leftIds: string[]
      rightIds: string[]
      bothIds: string[]
    }
  | {
      kind: 'fan_in'
      hubId: string
      groups: Map<string, string[]>
    }
  | { kind: 'pipeline' }
  | { kind: 'layered' }

function sortedIds(ids: Iterable<string>): string[] {
  return [...ids].sort((a, b) => a.localeCompare(b))
}

function neighborsByEdgeType(edges: GraphEdge[], hubId: string): Map<string, Set<string>> {
  const byType = new Map<string, Set<string>>()
  for (const edge of edges) {
    const other =
      edge.target === hubId ? edge.source : edge.source === hubId ? edge.target : null
    if (!other) continue
    const group = byType.get(edge.type) ?? new Set<string>()
    group.add(other)
    byType.set(edge.type, group)
  }
  return byType
}

/** Classify flow layout pattern from existing edge/entity types (frontend-only). */
export function classifyFlowLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
): FlowLayoutClassification {
  const hub = detectHubOpposing(nodes, edges, rootId)
  if (hub) return hub
  const fanIn = detectFanIn(nodes, edges, rootId)
  if (fanIn) return fanIn
  if (nodes.some((node) => ['endpoint', 'topic', 'table', 'function', 'class'].includes(node.type))) {
    return { kind: 'pipeline' }
  }
  return { kind: 'layered' }
}

function detectHubOpposing(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
): Extract<FlowLayoutClassification, { kind: 'hub_opposing' }> | null {
  const present = new Set(nodes.map((node) => node.id))
  const candidates = [
    rootId,
    ...nodes.filter((node) => node.type === 'topic').map((node) => node.id),
    ...sortedIds(present),
  ].filter((id, index, all) => present.has(id) && all.indexOf(id) === index)

  for (const hubId of candidates) {
    const byType = neighborsByEdgeType(edges, hubId)
    for (const [leftType, rightType] of OPPOSING_ROLES) {
      const left = sortedIds(byType.get(leftType) ?? [])
      const right = sortedIds(byType.get(rightType) ?? [])
      const bothIds = left.filter((id) => right.includes(id))
      const leftIds = left.filter((id) => !right.includes(id))
      const rightIds = right.filter((id) => !left.includes(id))
      if (leftIds.length === 0 || rightIds.length === 0) continue
      return { kind: 'hub_opposing', hubId, leftIds, rightIds, bothIds }
    }
  }
  return null
}

function detectFanIn(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
): Extract<FlowLayoutClassification, { kind: 'fan_in' }> | null {
  if (!nodes.some((node) => node.id === rootId)) return null
  const toRoot = edges.filter((edge) => edge.target === rootId && FAN_IN_TYPES.has(edge.type))
  const fromRoot = edges.filter((edge) => edge.source === rootId)
  if (toRoot.length < 2) return null
  if (fromRoot.length > toRoot.length) return null
  // Star-like catalogs only — deeper pipelines keep layered/pipeline layout.
  if (edges.length > toRoot.length + fromRoot.length) return null

  const groups = new Map<string, string[]>()
  for (const edge of toRoot) {
    const list = groups.get(edge.type) ?? []
    if (!list.includes(edge.source)) list.push(edge.source)
    groups.set(edge.type, list)
  }
  for (const [, list] of groups) list.sort((a, b) => a.localeCompare(b))
  return { kind: 'fan_in', hubId: rootId, groups }
}

function stackColumn(ids: string[], x: number, centerY: number): Map<string, Point> {
  const positions = new Map<string, Point>()
  const ordered = sortedIds(ids)
  ordered.forEach((id, index) => {
    positions.set(id, {
      x,
      y: centerY + (index - (ordered.length - 1) / 2) * FLOW_ROW,
    })
  })
  return positions
}

function layoutFanInPositions(hubId: string, groups: Map<string, string[]>): Map<string, Point> {
  const positions = new Map<string, Point>([[hubId, { x: 0, y: 0 }]])
  const roleEntries = [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  const splitRoles =
    roleEntries.length >= 2 && roleEntries.some(([, ids]) => ids.length >= 2)

  if (splitRoles) {
    roleEntries.forEach(([, ids], groupIndex) => {
      const wingX =
        roleEntries.length === 2
          ? groupIndex === 0
            ? -WING_X
            : WING_X
          : (groupIndex - (roleEntries.length - 1) / 2) * WING_X
      ids.forEach((id, index) => {
        positions.set(id, { x: wingX, y: -FLOW_ROW * (index + 1) })
      })
    })
    return positions
  }

  const all = sortedIds(roleEntries.flatMap(([, ids]) => ids))
  all.forEach((id, index) => {
    positions.set(id, {
      x: (index - (all.length - 1) / 2) * FLOW_COL,
      y: -FLOW_ROW,
    })
  })
  return positions
}

function wingBias(
  id: string,
  edges: GraphEdge[],
  leftIds: Set<string>,
  rightIds: Set<string>,
  hubId: string,
  seen = new Set<string>(),
): number {
  if (leftIds.has(id)) return -WING_X
  if (rightIds.has(id)) return WING_X
  if (seen.has(id)) return 0
  seen.add(id)
  const incoming = edges.filter((edge) => edge.target === id).map((edge) => edge.source)
  const scores = incoming.map((source) => {
    if (source === hubId) return 0
    if (leftIds.has(source)) return -WING_X
    if (rightIds.has(source)) return WING_X
    return wingBias(source, edges, leftIds, rightIds, hubId, new Set(seen))
  })
  if (!scores.length) return 0
  return scores.reduce((sum, value) => sum + value, 0) / scores.length
}

function layoutHubOpposingPositions(
  nodes: GraphNode[],
  edges: GraphEdge[],
  pattern: Extract<FlowLayoutClassification, { kind: 'hub_opposing' }>,
): Map<string, Point> {
  const { hubId, leftIds, rightIds, bothIds } = pattern
  const positions = new Map<string, Point>([[hubId, { x: 0, y: 0 }]])
  for (const [id, point] of stackColumn(leftIds, -WING_X, 0)) positions.set(id, point)
  for (const [id, point] of stackColumn(rightIds, WING_X, 0)) positions.set(id, point)
  bothIds.forEach((id, index) => {
    positions.set(id, { x: 0, y: FLOW_ROW * (index + 1) })
  })

  const leftSet = new Set(leftIds)
  const rightSet = new Set(rightIds)
  const placed = new Set(positions.keys())
  const levels = flowLevels(nodes, edges)
  const remaining = sortedIds(nodes.map((node) => node.id).filter((id) => !placed.has(id)))
  remaining.sort(
    (a, b) => (levels.get(a) ?? 0) - (levels.get(b) ?? 0) || a.localeCompare(b),
  )

  for (const id of remaining) {
    const preds = edges
      .filter((edge) => edge.target === id && positions.has(edge.source))
      .map((edge) => positions.get(edge.source)!)
    const bias = wingBias(id, edges, leftSet, rightSet, hubId)
    const y = preds.length
      ? Math.max(...preds.map((point) => point.y)) + FLOW_ROW
      : FLOW_ROW + (levels.get(id) ?? 1) * FLOW_ROW
    const x = preds.length
      ? preds.reduce((sum, point) => sum + point.x, 0) / preds.length
      : bias
    positions.set(id, { x, y })
  }
  return positions
}

function nodeRole(id: string, edges: GraphEdge[], byId: Map<string, GraphNode>): RoleWing {
  const node = byId.get(id)
  if (node && (node.type === 'config' || node.type === 'dependency')) return 'depends'
  const outgoing = edges.filter((edge) => edge.source === id)
  const reads = outgoing.some((edge) => edge.type === 'reads')
  const writes = outgoing.some((edge) => edge.type === 'writes')
  if (reads && !writes) return 'reads'
  if (writes && !reads) return 'writes'
  if (outgoing.length > 0 && outgoing.every((edge) => edge.type === 'depends_on')) return 'depends'
  return 'main'
}

const ROLE_ORDER: RoleWing[] = ['reads', 'main', 'writes', 'depends']

function architectureLevels(nodes: GraphNode[], edges: GraphEdge[]): Map<string, number> {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const directed = flowLevels(nodes, edges)
  const linked = new Set<string>()
  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target) || edge.source === edge.target) continue
    linked.add(edge.source)
    linked.add(edge.target)
  }
  const anchored = [...directed.entries()].filter(([id]) => linked.has(id))
  const last = anchored.length ? Math.max(...anchored.map(([, level]) => level)) : -1
  for (const node of nodes) {
    if (!linked.has(node.id)) directed.set(node.id, last + 1)
  }

  const keyed = new Map<string, number>()
  for (const node of nodes) {
    const topo = directed.get(node.id) ?? 0
    const rank = TYPE_RANK[node.type] ?? 6
    keyed.set(node.id, topo * 20 + rank)
  }
  const order = [...new Set(keyed.values())].sort((a, b) => a - b)
  const compact = new Map(order.map((value, index) => [value, index]))
  return new Map(nodes.map((node) => [node.id, compact.get(keyed.get(node.id)!) ?? 0]))
}

function layoutLayeredPositions(
  nodes: GraphNode[],
  edges: GraphEdge[],
  _rootId: string,
  mode: 'architecture' | 'flow',
  withRoleWings: boolean,
): { positions: Map<string, Point>; levels: Map<string, number> } {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const neighbors = new Map(nodes.map((node) => [node.id, new Set<string>()]))
  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) continue
    neighbors.get(edge.source)?.add(edge.target)
    neighbors.get(edge.target)?.add(edge.source)
  }

  const levels = mode === 'architecture' ? architectureLevels(nodes, edges) : flowLevels(nodes, edges)

  const columns: string[][] = []
  for (const node of nodes) {
    const level = levels.get(node.id) ?? 0
    ;(columns[level] ??= []).push(node.id)
  }
  const layers = columns.filter((column): column is string[] => column != null)
  for (const column of layers) column.sort((a, b) => a.localeCompare(b))

  for (let pass = 0; pass < 4; pass++) {
    const forward = pass % 2 === 0
    const indices = forward
      ? Array.from({ length: layers.length - 1 }, (_, i) => i + 1)
      : Array.from({ length: layers.length - 1 }, (_, i) => layers.length - i - 2)
    for (const columnIndex of indices) {
      const reference = layers[columnIndex + (forward ? -1 : 1)] ?? []
      const rank = new Map(reference.map((id, index) => [id, index]))
      const score = (id: string) => {
        const positions = [...(neighbors.get(id) ?? [])]
          .map((other) => rank.get(other))
          .filter((position): position is number => position !== undefined)
        return positions.length
          ? positions.reduce((sum, position) => sum + position, 0) / positions.length
          : Number.POSITIVE_INFINITY
      }
      layers[columnIndex]?.sort((a, b) => score(a) - score(b) || a.localeCompare(b))
    }
  }

  const positions = new Map<string, Point>()
  let cursorY = 0
  layers.forEach((column, level) => {
    const roleLists = new Map<RoleWing, string[]>()
    for (const id of column) {
      const role = withRoleWings ? nodeRole(id, edges, byId) : 'main'
      const list = roleLists.get(role) ?? []
      list.push(id)
      roleLists.set(role, list)
    }
    const presentRoles = ROLE_ORDER.filter((role) => (roleLists.get(role)?.length ?? 0) > 0)
    const split =
      withRoleWings &&
      mode === 'flow' &&
      column.length >= 3 &&
      presentRoles.length >= 2

    if (mode === 'architecture') {
      const rows = Math.max(1, Math.ceil(column.length / ARCH_PER_ROW))
      column.forEach((id, index) => {
        const row = Math.floor(index / ARCH_PER_ROW)
        const col = index % ARCH_PER_ROW
        const count = Math.min(ARCH_PER_ROW, column.length - row * ARCH_PER_ROW)
        positions.set(id, {
          x: (col - (count - 1) / 2) * ARCH_COL,
          y: cursorY + row * ARCH_ROW,
        })
      })
      cursorY += rows * ARCH_ROW + ARCH_LAYER_GAP
      return
    }

    if (!split) {
      column.forEach((id, index) => {
        positions.set(id, {
          x: (index - (column.length - 1) / 2) * FLOW_COL,
          y: level * FLOW_ROW,
        })
      })
      return
    }

    presentRoles.forEach((role, roleIndex) => {
      const ids = roleLists.get(role) ?? []
      const wingX = (roleIndex - (presentRoles.length - 1) / 2) * WING_X
      ids.forEach((id, index) => {
        positions.set(id, {
          x: wingX + (index - (ids.length - 1) / 2) * (FLOW_COL * 0.85),
          y: level * FLOW_ROW,
        })
      })
    })
  })
  return { positions, levels }
}

function toFlowNodes(
  nodes: GraphNode[],
  positions: Map<string, Point>,
  flow: boolean,
  levels?: Map<string, number>,
): RkgFlowNode[] {
  return sortedIds(nodes.map((node) => node.id)).map((id) => {
    const node = nodes.find((entry) => entry.id === id)!
    const position = positions.get(id) ?? { x: 0, y: 0 }
    const layer = levels?.get(id)
    return {
      id,
      type: 'rkg' as const,
      position,
      data: {
        label: node.label,
        entityType: node.type,
        qualifiedName: node.qualified_name,
        location: node.location,
        flow,
        ...(layer !== undefined ? { layer } : {}),
      },
    }
  })
}

const ENTRY_COL = 320
const ENTRY_ROW = 156
const DATA_TYPES = new Set(['table', 'config', 'dependency'])

/**
 * Whole-project overview: one vertical chain per entrypoint, shared data on the last row.
 * A single chain keeps the layered top-to-bottom placement.
 */
function layoutEntryColumns(
  nodes: GraphNode[],
  edges: GraphEdge[],
): { positions: Map<string, Point>; levels: Map<string, number> } | null {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const entries = nodes
    .filter((node) => node.type === 'endpoint' || node.type === 'topic')
    .sort((a, b) => a.label.localeCompare(b.label) || a.id.localeCompare(b.id))
  if (entries.length < 2) return null

  const outgoing = new Map<string, string[]>()
  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) continue
    if (edge.type === 'contains' || edge.type === 'imports') continue
    const list = outgoing.get(edge.source) ?? []
    if (!list.includes(edge.target)) list.push(edge.target)
    outgoing.set(edge.source, list)
  }
  for (const list of outgoing.values()) list.sort((a, b) => a.localeCompare(b))

  const reachedBy = new Map<string, Set<string>>()
  const walk = (entryId: string) => {
    const seen = new Set<string>([entryId])
    const queue = [entryId]
    while (queue.length) {
      const id = queue.shift()!
      for (const next of outgoing.get(id) ?? []) {
        if (seen.has(next)) continue
        seen.add(next)
        const owners = reachedBy.get(next) ?? new Set<string>()
        owners.add(entryId)
        reachedBy.set(next, owners)
        queue.push(next)
      }
    }
  }
  for (const entry of entries) walk(entry.id)

  const shared = new Set<string>()
  for (const [id, owners] of reachedBy) {
    const node = byId.get(id)
    if (node && DATA_TYPES.has(node.type) && owners.size >= 2) shared.add(id)
  }

  const columnOf = new Map<string, string>()
  for (const entry of entries) {
    columnOf.set(entry.id, entry.id)
    const seen = new Set<string>([entry.id])
    const queue = [entry.id]
    while (queue.length) {
      const id = queue.shift()!
      for (const next of outgoing.get(id) ?? []) {
        if (seen.has(next) || shared.has(next)) continue
        seen.add(next)
        if (!columnOf.has(next)) columnOf.set(next, entry.id)
        queue.push(next)
      }
    }
  }

  const positions = new Map<string, Point>()
  const levels = new Map<string, number>()
  let lowest = 0
  entries.forEach((entry, column) => {
    const members = nodes
      .map((node) => node.id)
      .filter((id) => columnOf.get(id) === entry.id && !shared.has(id))
    const depth = new Map<string, number>([[entry.id, 0]])
    const queue = [entry.id]
    while (queue.length) {
      const id = queue.shift()!
      for (const next of outgoing.get(id) ?? []) {
        if (columnOf.get(next) !== entry.id || depth.has(next)) continue
        depth.set(next, (depth.get(id) ?? 0) + 1)
        queue.push(next)
      }
    }
    const rows = new Map<number, string[]>()
    for (const id of members) {
      const row = depth.get(id) ?? 0
      const list = rows.get(row) ?? []
      list.push(id)
      rows.set(row, list)
    }
    let cursor = 0
    for (const row of [...rows.keys()].sort((a, b) => a - b)) {
      const ids = (rows.get(row) ?? []).sort((a, b) => a.localeCompare(b))
      ids.forEach((id, index) => {
        const y = cursor + index * ENTRY_ROW
        positions.set(id, { x: column * ENTRY_COL, y })
        levels.set(id, Math.round(y / ENTRY_ROW))
        lowest = Math.max(lowest, y)
      })
      cursor += ids.length * ENTRY_ROW + 28
    }
  })

  const sharedIds = [...shared].sort((a, b) => a.localeCompare(b))
  const loose = nodes
    .map((node) => node.id)
    .filter((id) => !positions.has(id) && !shared.has(id))
    .sort((a, b) => a.localeCompare(b))
  const tail = [...sharedIds, ...loose]
  const tailY = lowest + ENTRY_ROW + 36
  tail.forEach((id, index) => {
    const row = Math.floor(index / ARCH_PER_ROW)
    const col = index % ARCH_PER_ROW
    const count = Math.min(ARCH_PER_ROW, tail.length - row * ARCH_PER_ROW)
    const y = tailY + row * ENTRY_ROW
    positions.set(id, {
      x: (col - (count - 1) / 2) * ARCH_COL + ((entries.length - 1) * ENTRY_COL) / 2,
      y,
    })
    levels.set(id, Math.round(y / ENTRY_ROW))
  })
  return { positions, levels }
}

/** Stable layout: pattern-aware in flow mode, top-down strata in architecture mode. */
export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
  mode: 'architecture' | 'flow' = 'architecture',
): RkgFlowNode[] {
  if (mode === 'architecture') {
    const columns = layoutEntryColumns(nodes, edges)
    if (columns) return toFlowNodes(nodes, columns.positions, true, columns.levels)
    const laid = layoutLayeredPositions(nodes, edges, rootId, mode, false)
    return toFlowNodes(nodes, laid.positions, true, laid.levels)
  }

  const pattern = classifyFlowLayout(nodes, edges, rootId)
  if (pattern.kind === 'hub_opposing') {
    return toFlowNodes(nodes, layoutHubOpposingPositions(nodes, edges, pattern), true)
  }
  if (pattern.kind === 'fan_in') {
    return toFlowNodes(nodes, layoutFanInPositions(pattern.hubId, pattern.groups), true)
  }
  const laid = layoutLayeredPositions(nodes, edges, rootId, 'flow', pattern.kind === 'pipeline')
  return toFlowNodes(nodes, laid.positions, true, laid.levels)
}
