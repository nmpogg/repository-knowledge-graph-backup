import type { EdgeDirection, EdgeType } from '../types/api'
import type { MessageKey } from '../i18n'

export interface GraphPreset {
  id: string
  labelKey: MessageKey
  descriptionKey: MessageKey
  direction: EdgeDirection
  edge_types: EdgeType[]
  max_depth: number
  /** When true, hide this preset unless the snapshot has HTTP/DB semantics. */
  requiresDataPath?: boolean
}

export const GRAPH_PRESETS: GraphPreset[] = [
  {
    id: 'api_to_db',
    labelKey: 'preset.api_to_db.label',
    descriptionKey: 'preset.api_to_db.description',
    direction: 'outgoing',
    edge_types: ['handled_by', 'calls', 'depends_on', 'reads', 'writes'],
    max_depth: 6,
    requiresDataPath: true,
  },
  {
    id: 'ui_to_api',
    labelKey: 'preset.ui_to_api.label',
    descriptionKey: 'preset.ui_to_api.description',
    direction: 'outgoing',
    edge_types: ['handled_by', 'calls', 'depends_on'],
    max_depth: 6,
  },
  {
    id: 'event_participants',
    labelKey: 'preset.event_participants.label',
    descriptionKey: 'preset.event_participants.description',
    direction: 'both',
    edge_types: ['publishes', 'consumes'],
    max_depth: 1,
  },
  {
    id: 'topic_flow',
    labelKey: 'preset.topic_flow.label',
    descriptionKey: 'preset.topic_flow.description',
    direction: 'both',
    edge_types: ['consumes', 'publishes', 'calls', 'reads', 'writes'],
    max_depth: 6,
  },
  {
    id: 'config_users',
    labelKey: 'preset.config_users.label',
    descriptionKey: 'preset.config_users.description',
    direction: 'incoming',
    edge_types: ['depends_on'],
    max_depth: 1,
  },
  {
    id: 'interface_implementations',
    labelKey: 'preset.interface_implementations.label',
    descriptionKey: 'preset.interface_implementations.description',
    direction: 'incoming',
    edge_types: ['implements', 'inherits_from'],
    max_depth: 1,
  },
]
