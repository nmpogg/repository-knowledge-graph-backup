import {
  Handle,
  Position,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import type { EntityType } from '../../types/api'

export type GraphNodeData = {
  label: string
  entityType: EntityType
  qualifiedName: string
  location?: string
  flow?: boolean
}

export type RkgFlowNode = Node<GraphNodeData, 'rkg'>

export function RkgEntityNode({ data, selected }: NodeProps<RkgFlowNode>) {
  return (
    <div
      className={`rkg-node${data.flow ? ' flow-step' : ''}${selected ? ' selected' : ''}`}
      data-kind={data.entityType}
    >
      <Handle type="target" position={Position.Left} id="target-left" className="graph-node-handle" aria-hidden />
      <Handle type="target" position={Position.Right} id="target-right" className="graph-node-handle" aria-hidden />
      <Handle type="target" position={Position.Top} id="target-top" className="graph-node-handle" aria-hidden />
      <Handle type="target" position={Position.Bottom} id="target-bottom" className="graph-node-handle" aria-hidden />
      <span className="type">{data.entityType}</span>
      <div className="label" title={data.qualifiedName}>{data.label}</div>
      {data.location ? <div className="graph-node-location" title={data.location}>{data.location}</div> : null}
      <Handle type="source" position={Position.Left} id="source-left" className="graph-node-handle" aria-hidden />
      <Handle type="source" position={Position.Right} id="source-right" className="graph-node-handle" aria-hidden />
      <Handle type="source" position={Position.Top} id="source-top" className="graph-node-handle" aria-hidden />
      <Handle type="source" position={Position.Bottom} id="source-bottom" className="graph-node-handle" aria-hidden />
    </div>
  )
}

export const nodeTypes = { rkg: RkgEntityNode }
