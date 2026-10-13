import { BaseEdge, EdgeLabelRenderer, type EdgeProps } from '@xyflow/react'
import type { CSSProperties } from 'react'

export type RelationshipEdgeData = {
  label: string
  color: string
  focused: boolean
  muted: boolean
  flowing: boolean
  lane: number
  showLabel: boolean
  vertical?: boolean
  bypassX?: number
}

export function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
  data,
}: EdgeProps) {
  const relation = data as RelationshipEdgeData | undefined
  const lane = relation?.lane ?? 0
  const dx = targetX - sourceX
  const bend = lane * 34
  const vertical = relation?.vertical || Math.abs(dx) < 100
  const direction = dx >= 0 ? 1 : -1
  const controlX = Math.max(56, Math.abs(dx) * 0.42)
  const controlY = Math.max(36, Math.abs(targetY - sourceY) * 0.42)
  const verticalDirection = targetY >= sourceY ? 1 : -1
  const bypass = relation?.bypassX
  const path = bypass !== undefined
    ? `M ${sourceX},${sourceY} L ${sourceX},${sourceY + 18} L ${bypass},${sourceY + 18} L ${bypass},${targetY - 18} L ${targetX},${targetY - 18} L ${targetX},${targetY}`
    : vertical
    ? `M ${sourceX},${sourceY} C ${sourceX + bend},${sourceY + verticalDirection * controlY} ${targetX + bend},${targetY - verticalDirection * controlY} ${targetX},${targetY}`
    : `M ${sourceX},${sourceY} C ${sourceX + direction * controlX},${sourceY + bend} ${targetX - direction * controlX},${targetY + bend} ${targetX},${targetY}`
  const labelX = bypass ?? (sourceX + targetX) / 2 + (vertical ? bend * 0.75 : 0)
  const labelY = (sourceY + targetY) / 2 + (bypass !== undefined ? lane * 24 : vertical ? 0 : bend * 0.75)
  const style = {
    '--relation-color': relation?.color ?? 'var(--graph-edge)',
  } as CSSProperties

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        className={`relationship-edge${relation?.focused ? ' is-focused' : ''}${relation?.muted ? ' is-muted' : ''}`}
        style={style}
      />
      {relation?.flowing ? (
        <path
          d={path}
          className="relationship-edge-flow"
          style={style}
        />
      ) : null}
      {relation?.showLabel ? (
        <EdgeLabelRenderer>
          <span
            className={`relationship-label${relation.focused ? ' is-focused' : ''}`}
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`, borderColor: relation.color }}
          >
            {relation.label}
          </span>
        </EdgeLabelRenderer>
      ) : null}
    </>
  )
}
