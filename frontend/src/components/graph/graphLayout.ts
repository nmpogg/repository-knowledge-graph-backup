import type { GraphEdge, GraphNode } from '../../types/api'
import type { RkgFlowNode } from './RkgEntityNode'
import { flowLevels } from './flowPresentation'

const COLUMN_GAP = 318
const ROW_GAP = 104
const FLOW_ROW = 132
const FLOW_COL = 244
const WING_X = 280

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

function layoutLayeredPositions(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
  mode: 'architecture' | 'flow',
  withRoleWings: boolean,
): Map<string, Point> {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const neighbors = new Map(nodes.map((node) => [node.id, new Set<string>()]))
  for (const edge of edges) {
    if (!byId.has(edge.source) || !byId.has(edge.target)) continue
    neighbors.get(edge.source)?.add(edge.target)
    neighbors.get(edge.target)?.add(edge.source)
  }

  const levels = mode === 'flow' ? flowLevels(nodes, edges) : new Map<string, number>()
  const queue = mode === 'architecture' && byId.has(rootId) ? [rootId] : []
  if (queue.length) levels.set(rootId, 0)
  for (let index = 0; index < queue.length; index++) {
    const id = queue[index]
    const adjacent = [...(neighbors.get(id) ?? [])].sort()
    for (const other of adjacent) {
      if (levels.has(other)) continue
      levels.set(other, (levels.get(id) ?? 0) + 1)
      queue.push(other)
    }
  }

  const disconnected = nodes.filter((node) => !levels.has(node.id)).sort((a, b) => a.id.localeCompare(b.id))
  const lastLevel = Math.max(0, ...levels.values())
  disconnected.forEach((node) => levels.set(node.id, lastLevel + 1))

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

    if (!split) {
      column.forEach((id, index) => {
        positions.set(id, {
          x: mode === 'flow' ? (index - (column.length - 1) / 2) * FLOW_COL : level * COLUMN_GAP,
          y: mode === 'flow' ? level * FLOW_ROW : (index - (column.length - 1) / 2) * ROW_GAP,
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
  return positions
}

function toFlowNodes(
  nodes: GraphNode[],
  positions: Map<string, Point>,
  flow: boolean,
): RkgFlowNode[] {
  return sortedIds(nodes.map((node) => node.id)).map((id) => {
    const node = nodes.find((entry) => entry.id === id)!
    const position = positions.get(id) ?? { x: 0, y: 0 }
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
      },
    }
  })
}

/** Stable layout: pattern-aware in flow mode, layered BFS in architecture mode. */
export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rootId: string,
  mode: 'architecture' | 'flow' = 'architecture',
): RkgFlowNode[] {
  if (mode === 'architecture') {
    return toFlowNodes(nodes, layoutLayeredPositions(nodes, edges, rootId, mode, false), false)
  }

  const pattern = classifyFlowLayout(nodes, edges, rootId)
  if (pattern.kind === 'hub_opposing') {
    return toFlowNodes(nodes, layoutHubOpposingPositions(nodes, edges, pattern), true)
  }
  if (pattern.kind === 'fan_in') {
    return toFlowNodes(nodes, layoutFanInPositions(pattern.hubId, pattern.groups), true)
  }
  return toFlowNodes(
    nodes,
    layoutLayeredPositions(nodes, edges, rootId, 'flow', pattern.kind === 'pipeline'),
    true,
  )
}
