import type { GraphEdge, GraphNode } from '../../types/api'

const HTTP_CLIENT_LEAVES = new Set([
  'get',
  'put',
  'post',
  'patch',
  'delete',
  'request',
  'fetch',
])

/** Ownership supplies a breadcrumb on a flow step, never a competing graph branch. */
export function flowPresentation(nodes: GraphNode[], edges: GraphEdge[], rootId: string, showStructure: boolean) {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const root = byId.get(rootId)
  const navigationRoot = root?.attributes?.kind === 'navigation'
  const semanticEdges = edges.filter((edge) => edge.type !== 'imports' && (
    edge.type !== 'contains' || edge.source === rootId && ['class', 'interface'].includes(byId.get(rootId)?.type ?? '')
  ))
  const ids = new Set([rootId, ...semanticEdges.flatMap((edge) => [edge.source, edge.target])])
  const parents = new Map<string, GraphNode[]>()
  for (const edge of edges.filter((edge) => edge.type === 'contains')) {
    const parent = byId.get(edge.source)
    if (parent) parents.set(edge.target, [...(parents.get(edge.target) ?? []), parent])
  }
  function location(node: GraphNode) {
    if (node.file_path) return node.file_path
    const queue = [...(parents.get(node.id) ?? [])]
    const seen = new Set<string>()
    while (queue.length) {
      const parent = queue.shift()!
      if (seen.has(parent.id)) continue
      seen.add(parent.id)
      if (parent.type === 'file') return parent.file_path || parent.qualified_name || parent.label
      queue.push(...(parents.get(parent.id) ?? []))
    }
    return ''
  }
  return {
    nodes: nodes.filter((node) => ids.has(node.id)).map((node) => {
      const parts = node.qualified_name.replace(/:/g, '.').split('.')
      const owner = parts.at(-2) ?? ''
      let label = node.type === 'function' && /^[A-Z]/.test(owner)
        ? `${owner}.${parts.at(-1)}` : node.label
      // HTTP endpoints: prefer METHOD path (Detail already shows this; graph should match).
      if (node.type === 'endpoint' && node.attributes?.kind !== 'navigation') {
        const method = node.attributes?.method
        const path =
          (typeof node.attributes?.path === 'string' && node.attributes.path) ||
          (typeof node.attributes?.route_path === 'string' && node.attributes.route_path) ||
          null
        if (method && path) label = `${method} ${path}`
        else if (path) label = path
      }
      // Navigation UI→API: surface evidence-based request on the API callable.
      if (navigationRoot && node.type === 'function') {
        const requests = node.attributes?.http_requests?.split('|').map((p) => p.trim()).filter(Boolean)
        if (requests?.length) {
          label = requests.length === 1 ? requests[0]! : requests.join(' · ')
        } else {
          const leaf = (node.label.includes('.') ? node.label.split('.').pop()! : node.label).toLowerCase()
          if (HTTP_CLIENT_LEAVES.has(leaf)) {
            label = leaf.toUpperCase() === 'REQUEST' || leaf.toUpperCase() === 'FETCH'
              ? leaf
              : leaf.toUpperCase()
          }
        }
      }
      return { ...node, label, location: showStructure ? location(node) : undefined }
    }),
    edges: semanticEdges,
  }
}

/** Condense call cycles, then place steps after all predecessors, not nearest hop. */
export function flowLevels(nodes: GraphNode[], edges: GraphEdge[]) {
  const adjacency = new Map(nodes.map((node) => [node.id, [] as string[]]))
  for (const edge of edges) if (adjacency.has(edge.source) && adjacency.has(edge.target)) adjacency.get(edge.source)!.push(edge.target)
  const indices = new Map<string, number>(), low = new Map<string, number>()
  const stack: string[] = [], active = new Set<string>(), components: string[][] = []
  function visit(id: string) {
    indices.set(id, indices.size); low.set(id, indices.get(id)!)
    stack.push(id); active.add(id)
    for (const other of [...adjacency.get(id)!].sort()) {
      if (!indices.has(other)) { visit(other); low.set(id, Math.min(low.get(id)!, low.get(other)!)) }
      else if (active.has(other)) low.set(id, Math.min(low.get(id)!, indices.get(other)!))
    }
    if (low.get(id) !== indices.get(id)) return
    const group: string[] = []
    let member: string
    do { member = stack.pop()!; active.delete(member); group.push(member) } while (member !== id)
    components.push(group.sort())
  }
  for (const id of [...adjacency.keys()].sort()) if (!indices.has(id)) visit(id)
  const componentOf = new Map(components.flatMap((group, index) => group.map((id) => [id, index] as const)))
  const outgoing = components.map(() => new Set<number>()), incoming = components.map(() => 0)
  for (const edge of edges) {
    const from = componentOf.get(edge.source), to = componentOf.get(edge.target)
    if (from === undefined || to === undefined || from === to || outgoing[from].has(to)) continue
    outgoing[from].add(to); incoming[to]++
  }
  const layers = components.map(() => 0)
  const queue = components.map((_, index) => index).filter((index) => incoming[index] === 0)
  for (let i = 0; i < queue.length; i++) for (const next of outgoing[queue[i]]) {
    layers[next] = Math.max(layers[next], layers[queue[i]] + 1)
    if (--incoming[next] === 0) queue.push(next)
  }
  const levels = new Map(nodes.map((node) => [node.id, layers[componentOf.get(node.id)!]]))
  const lastCall = Math.max(0, ...nodes.filter((node) => !['table', 'topic', 'config', 'dependency'].includes(node.type)).map((node) => levels.get(node.id)!))
  for (const node of nodes) if (['table', 'topic', 'config', 'dependency'].includes(node.type) && adjacency.get(node.id)!.length === 0) {
    levels.set(node.id, Math.max(levels.get(node.id)!, lastCall + 1))
  }
  return levels
}
