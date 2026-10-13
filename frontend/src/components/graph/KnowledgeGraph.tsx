import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  Panel,
  ReactFlow,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
} from '@xyflow/react'
import { Maximize2 } from 'lucide-react'
import { useEffect, useMemo, useRef } from 'react'
import type { GraphEdge, GraphNode } from '../../types/api'
import { layoutGraph } from './graphLayout'
import { flowPresentation } from './flowPresentation'
import { RelationshipEdge, type RelationshipEdgeData } from './RelationshipEdge'
import { nodeTypes, type RkgFlowNode } from './RkgEntityNode'

const RELATION_COLORS: Record<string, string> = {
  handled_by: '#2563eb',
  calls: '#7c3aed',
  depends_on: '#64748b',
  reads: '#0f766e',
  writes: '#b45309',
  publishes: '#be185d',
  consumes: '#be185d',
  implements: '#475569',
  inherits_from: '#475569',
}

export function relationAccent(type: string): string {
  return RELATION_COLORS[type] ?? '#64748b'
}

const relationshipEdgeTypes = { relationship: RelationshipEdge }

function toEdges(
  edges: GraphEdge[],
  focusId: string,
  selectedId: string | null,
  focusOnly: boolean,
  nodes: RkgFlowNode[],
  flow: boolean,
): Edge[] {
  const positions = new Map(nodes.map((node) => [node.id, node.position]))
  const siblings = new Map<string, GraphEdge[]>()
  for (const edge of edges) {
    const key = `${edge.source}\u0000${edge.target}`
    const group = siblings.get(key) ?? []
    group.push(edge)
    siblings.set(key, group)
  }
  return edges.map((edge) => {
    const group = siblings.get(`${edge.source}\u0000${edge.target}`) ?? [edge]
    const lane = group.indexOf(edge) - (group.length - 1) / 2
    const focused = edge.source === focusId || edge.target === focusId
    const color = relationAccent(edge.type)
    const source = positions.get(edge.source)
    const target = positions.get(edge.target)
    const dx = source && target ? target.x - source.x : 0
    const dy = source && target ? target.y - source.y : 0
    // Prefer the dominant axis so hub wings (left/right) and pipelines (top/bottom) both route cleanly.
    const vertical = !source || !target ? true : Math.abs(dy) >= Math.abs(dx) * 0.65
    const sourceSide = vertical
      ? (dy >= 0 ? 'bottom' : 'top')
      : (dx >= 0 ? 'right' : 'left')
    const targetSide = vertical
      ? (dy >= 0 ? 'top' : 'bottom')
      : (dx >= 0 ? 'left' : 'right')
    const data: RelationshipEdgeData = {
      label: edge.label || edge.type,
      color,
      lane,
      focused,
      muted: focusOnly && !focused,
      flowing: !flow && selectedId != null && (edge.source === selectedId || edge.target === selectedId),
      showLabel: flow || focused || (!focusOnly && edges.length <= 12),
      vertical,
      bypassX: flow && vertical && source && target && dy > 140
        ? source.x + (dx >= 0 ? 222 : -22) + lane * 8 : undefined,
    }
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: `source-${sourceSide}`,
      targetHandle: `target-${targetSide}`,
      type: 'relationship',
      data,
      markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color },
    }
  })
}

function FitAllButton() {
  const { fitView } = useReactFlow()
  return (
    <button
      type="button"
      className="graph-fit-btn"
      onClick={() => void fitView({ padding: 0.18, duration: 280 })}
      title="Fit entire graph"
    >
      <Maximize2 size={15} aria-hidden />
      Fit all
    </button>
  )
}

/** Keep the graph / focus node centered in the canvas when data or selection changes. */
function GraphCamera({
  rootId,
  selectedId,
  nodeCount,
  edgeCount,
  layoutKey,
  mode,
  locations,
}: {
  rootId: string
  selectedId: string | null
  nodeCount: number
  edgeCount: number
  layoutKey: number
  mode: 'architecture' | 'flow'
  locations: boolean
}) {
  const { fitView, setCenter, getNode } = useReactFlow()
  const lastGraphSig = useRef('')
  const graphSig = `${rootId}:${nodeCount}:${edgeCount}:${layoutKey}:${mode}:${locations}`

  useEffect(() => {
    const graphChanged = lastGraphSig.current !== graphSig
    lastGraphSig.current = graphSig

    const id = window.requestAnimationFrame(() => {
      if (graphChanged) {
        void fitView({ padding: mode === 'flow' ? 0.06 : 0.18, duration: 280 })
        return
      }
      if (mode === 'flow') return
      const focusId = selectedId ?? rootId
      const node = getNode(focusId)
      if (!node) {
        void fitView({ padding: 0.18, duration: 280 })
        return
      }
      const w = node.measured?.width ?? node.width ?? 160
      const h = node.measured?.height ?? node.height ?? 56
      void setCenter(node.position.x + w / 2, node.position.y + h / 2, {
        zoom: Math.max(0.85, Math.min(1.15, 1)),
        duration: 280,
      })
    })
    return () => window.cancelAnimationFrame(id)
  }, [graphSig, selectedId, rootId, fitView, setCenter, getNode])

  return null
}

export function KnowledgeGraph({
  nodes,
  edges,
  rootId,
  selectedId,
  onSelect,
  mode = 'architecture',
  showStructure = false,
  focusOnly,
  layoutKey = 0,
}: {
  nodes: GraphNode[]
  edges: GraphEdge[]
  rootId: string
  selectedId: string | null
  onSelect: (id: string) => void
  mode?: 'architecture' | 'flow'
  showStructure?: boolean
  /** Dim nodes and edges that are not direct links of the selected entity. */
  focusOnly: boolean
  /** Bump when side panels open/close so fitView re-centers. */
  layoutKey?: number
}) {
  const effectiveMode = mode
  const presentation = useMemo(() => effectiveMode === 'flow'
    ? flowPresentation(nodes, edges, rootId, showStructure) : { nodes, edges },
  [nodes, edges, rootId, showStructure, effectiveMode])
  const focusId = selectedId ?? rootId
  const initialNodes = useMemo(() => layoutGraph(presentation.nodes, presentation.edges, rootId, effectiveMode), [presentation, rootId, effectiveMode])
  const initialEdges = useMemo(
    () => toEdges(presentation.edges, focusId, selectedId, focusOnly, initialNodes, effectiveMode === 'flow'),
    [presentation, focusId, selectedId, focusOnly, initialNodes, effectiveMode],
  )
  const relations = useMemo(
    () => edges.filter((edge) => edge.source === focusId || edge.target === focusId),
    [edges, focusId],
  )

  const [flowNodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    setNodes(initialNodes)
  }, [initialNodes, setNodes])

  useEffect(() => {
    setNodes((current) => current.map((node) => ({
      ...node,
      selected: node.id === focusId,
      className: focusOnly && node.id !== focusId && !relations.some((edge) => edge.source === node.id || edge.target === node.id)
        ? 'graph-node-muted'
        : undefined,
    })))
  }, [focusId, focusOnly, relations, setNodes])

  useEffect(() => {
    setEdges(initialEdges)
  }, [initialEdges, setEdges])

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      edgeTypes={relationshipEdgeTypes}
      fitView
      fitViewOptions={{ padding: effectiveMode === 'flow' ? 0.06 : 0.18 }}
      minZoom={0.2}
      maxZoom={1.8}
      onNodeClick={(_, node) => onSelect(node.id)}
      proOptions={{ hideAttribution: true }}
      aria-label="Knowledge graph canvas"
      key={layoutKey}
    >
      <Background gap={24} size={1} color="var(--graph-dot)" />
      <Controls showInteractive={false} position="bottom-left" style={{ display: 'none' }} />
      <MiniMap
        pannable
        zoomable
        position="bottom-right"
        nodeStrokeWidth={2}
        maskColor="color-mix(in srgb, var(--color-background) 72%, transparent)"
        style={{ display: 'none', borderRadius: 8, overflow: 'hidden' }}
      />
      <Panel position="top-right">
        <FitAllButton />
      </Panel>
      <GraphCamera
        rootId={rootId}
        selectedId={selectedId}
        nodeCount={presentation.nodes.length}
        edgeCount={presentation.edges.length}
        layoutKey={layoutKey}
        mode={effectiveMode}
        locations={showStructure}
      />
    </ReactFlow>
  )
}
