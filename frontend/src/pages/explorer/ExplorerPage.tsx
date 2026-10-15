import { AnimatePresence, motion } from 'framer-motion'
import {
  ChevronLeft,
  ChevronRight,
  Download,
  LayoutDashboard,
  List,
  ListTree,
  Maximize2,
  MessageSquare,
  Network,
  PanelLeft,
  PanelRight,
  Search,
  Settings2,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import {
  Link,
  Navigate,
  Route,
  Routes,
  UNSAFE_LocationContext,
  UNSAFE_NavigationContext,
  UNSAFE_RouteContext,
  UNSAFE_createMemoryHistory,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'
import { ConversationPage } from '../conversations/ConversationPage'
import { ConversationsPage } from '../conversations/ConversationsPage'
import { ReactFlowProvider } from '@xyflow/react'
import { getRkgClient } from '../../client'
import { DEMO_SNAPSHOT_ID } from '../../client/mock/fixtures'
import { KnowledgeGraph, relationAccent } from '../../components/graph/KnowledgeGraph'
import { PROJECT_OVERVIEW_ROOT_ID, exportProjectOverview, loadProjectOverview } from '../../components/graph/projectOverview'
import { SnapshotStructure } from './SnapshotStructure'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { useLocale } from '../../i18n'
import { formatError, shortId } from '../../lib/format'
import {
  endpointDisplayLabel,
  endpointEntryKind,
  flowPresetIdForEntry,
  isPartialUiFlow,
  outboundRequestsFromFlow,
  outboundResponsesFromFlow,
  routeOutboundRequests,
  routeOutboundResponses,
  routePageHandler,
  routeSignal,
  snapshotSupportsApiToDb,
} from '../../lib/endpointKind'
import { GRAPH_PRESETS } from '../../lib/presets'
import type {
  ContextExport,
  EdgeType,
  EntityDetail,
  EntitySummary,
  Repository,
  SubgraphResponse,
} from '../../types/api'
import { RkgApiError } from '../../types/api'

type ViewMode = 'graph' | 'list' | 'structure'

function downloadJson(value: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const panelMotion = {
  left: {
    initial: { width: 0, opacity: 0 },
    animate: { width: 280, opacity: 1 },
    exit: { width: 0, opacity: 0 },
  },
  right: {
    initial: { width: 0, opacity: 0 },
    animate: { width: 320, opacity: 1 },
    exit: { width: 0, opacity: 0 },
  },
}

export function ExplorerPage() {
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const [params, setParams] = useSearchParams()

  const snapshotId = params.get('snapshot_id') ?? ''

  const [repo, setRepo] = useState<Repository | null>(null)
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [results, setResults] = useState<EntitySummary[]>([])
  const [rootId, setRootId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<EntityDetail | null>(null)
  const [graph, setGraph] = useState<SubgraphResponse | null>(null)
  const graphRequest = useRef(0)
  const viewRequest = useRef(0)
  const [depth, setDepth] = useState(6)
  const [maxNodes, setMaxNodes] = useState(50)
  const [edgeTypes, setEdgeTypes] = useState<EdgeType[] | undefined>(undefined)
  const [graphView, setGraphView] = useState<'flow' | 'neighborhood'>('flow')
  const [overviewGraph, setOverviewGraph] = useState(false)
  const [includeStructure, setIncludeStructure] = useState(false)
  const [includeDependencies, setIncludeDependencies] = useState(false)
  const [activePreset, setActivePreset] = useState<string>('')
  const [view, setView] = useState<ViewMode>('list')
  const [apis, setApis] = useState<EntitySummary[]>([])
  const [apisLoading, setApisLoading] = useState(false)
  const [hasDataResource, setHasDataResource] = useState(false)
  const [entryFilter, setEntryFilter] = useState<'all' | 'http' | 'navigation' | 'messaging'>('all')
  const entryFilterInitialized = useRef(false)
  /** Lazy UI→API request lines when adapter attribute is absent (existing snapshots). */
  const [routeRequests, setRouteRequests] = useState<Record<string, string[]>>({})
  const [routeRequestsLoading, setRouteRequestsLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exportOpen, setExportOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exported, setExported] = useState<ContextExport | null>(null)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [askOpen, setAskOpen] = useState(false)
  const [askMounted, setAskMounted] = useState(false)
  const [snapshotSchema, setSnapshotSchema] = useState<string | undefined>()
  const [askEntry, setAskEntry] = useState<string | null>(null)
  const [askSession, setAskSession] = useState(0)
  const askOpenToken = useRef(0)
  const [layoutKey, setLayoutKey] = useState(0)
  const [focusOnly, setFocusOnly] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setSnapshotSchema(undefined)
      if (!snapshotId) {
        setRepo(null)
        return
      }
      try {
        const list = await client.listRepositories({ limit: 100 })
        for (const r of list.items) {
          const snaps = await client.listSnapshots(r.repository_id, { limit: 50 })
          const snapshot = snaps.items.find((s) => s.snapshot_id === snapshotId)
          if (snapshot) {
            if (!cancelled) {
              setRepo(r)
              setSnapshotSchema(snapshot.schema_version)
            }
            return
          }
        }
        if (!cancelled) setRepo(list.items[0] ?? null)
      } catch {
        if (!cancelled) setRepo(null)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, snapshotId])

  const runSearch = useCallback(async () => {
    if (!snapshotId) return
    setSearchLoading(true)
    try {
      const page = await client.searchEntities(snapshotId, {
        q: query || undefined,
        type: typeFilter || undefined,
        limit: 40,
      })
      setResults(page.items)
    } catch (err) {
      if (err instanceof RkgApiError && err.code === 'snapshot_unavailable') {
        setError(err.message)
      } else {
        setError(formatError(err, locale))
      }
    } finally {
      setSearchLoading(false)
    }
  }, [client, snapshotId, query, typeFilter, locale])

  useEffect(() => {
    if (!snapshotId) {
      setApis([])
      setHasDataResource(false)
      entryFilterInitialized.current = false
      return
    }
    let cancelled = false
    setApisLoading(true)
    void (async () => {
      try {
        const [page, topics, tables] = await Promise.all([
          client.searchEntities(snapshotId, { type: 'endpoint', limit: 100 }),
          client.searchEntities(snapshotId, { type: 'topic', limit: 100 }),
          client.searchEntities(snapshotId, { type: 'table', limit: 1 }),
        ])
        if (cancelled) return
        setApis([...page.items, ...topics.items])
        setHasDataResource(tables.items.length > 0)
      } catch {
        if (!cancelled) {
          setApis([])
          setHasDataResource(false)
        }
      } finally {
        if (!cancelled) setApisLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, snapshotId])

  useEffect(() => {
    if (!snapshotId) return
    void runSearch()
  }, [snapshotId, runSearch])

  const entryGroups = useMemo(() => {
    const http: EntitySummary[] = []
    const navigation: EntitySummary[] = []
    const messaging: EntitySummary[] = []
    const other: EntitySummary[] = []
    for (const item of apis) {
      const kind = endpointEntryKind(item)
      if (kind === 'http') http.push(item)
      else if (kind === 'navigation') navigation.push(item)
      else if (kind === 'messaging') messaging.push(item)
      else other.push(item)
    }
    return { http, navigation, messaging, other }
  }, [apis])

  const visibleEntries = useMemo(() => {
    if (entryFilter === 'http') return entryGroups.http
    if (entryFilter === 'navigation') return entryGroups.navigation
    if (entryFilter === 'messaging') return entryGroups.messaging
    return [
      ...entryGroups.http,
      ...entryGroups.navigation,
      ...entryGroups.messaging,
      ...entryGroups.other,
    ]
  }, [entryFilter, entryGroups])

  const showEntryTabs =
    [entryGroups.http.length > 0, entryGroups.navigation.length > 0, entryGroups.messaging.length > 0].filter(
      Boolean,
    ).length >= 2

  const uiOnlyCatalog =
    entryGroups.navigation.length > 0 &&
    entryGroups.http.length === 0 &&
    entryGroups.messaging.length === 0

  const messagingOnlyCatalog =
    entryGroups.messaging.length > 0 &&
    entryGroups.http.length === 0 &&
    entryGroups.navigation.length === 0

  const apiToDbAvailable = snapshotSupportsApiToDb(apis, hasDataResource)

  const visiblePresets = useMemo(
    () =>
      GRAPH_PRESETS.filter(
        (preset) => !(preset.requiresDataPath && !apiToDbAvailable),
      ),
    [apiToDbAvailable],
  )

  useEffect(() => {
    if (apisLoading || entryFilterInitialized.current || apis.length === 0) return
    entryFilterInitialized.current = true
    if (entryGroups.http.length === 0 && entryGroups.navigation.length > 0 && entryGroups.messaging.length === 0) {
      setEntryFilter('navigation')
    } else if (
      entryGroups.messaging.length > 0 &&
      entryGroups.http.length === 0 &&
      entryGroups.navigation.length === 0
    ) {
      setEntryFilter('messaging')
    } else {
      setEntryFilter('all')
    }
  }, [
    apisLoading,
    apis.length,
    entryGroups.http.length,
    entryGroups.navigation.length,
    entryGroups.messaging.length,
  ])

  useEffect(() => {
    if (!snapshotId || apisLoading) {
      setRouteRequests({})
      setRouteRequestsLoading(false)
      return
    }
    const needs = entryGroups.navigation.filter(
      (item) => routeOutboundRequests(item).length === 0,
    )
    if (needs.length === 0) {
      setRouteRequests({})
      setRouteRequestsLoading(false)
      return
    }
    let cancelled = false
    setRouteRequestsLoading(true)
    void (async () => {
      const next: Record<string, string[]> = {}
      const preset = GRAPH_PRESETS.find((item) => item.id === 'ui_to_api')
      const chunk = 4
      for (let i = 0; i < needs.length && !cancelled; i += chunk) {
        const batch = needs.slice(i, i + chunk)
        await Promise.all(
          batch.map(async (item) => {
            try {
              const g = await client.getSubgraph({
                snapshot_id: snapshotId,
                root_id: item.id,
                direction: 'both',
                edge_types: preset?.edge_types ?? ['handled_by', 'calls', 'depends_on'],
                depth: preset?.max_depth ?? 6,
                max_nodes: 40,
                view: 'flow',
                include_structure: false,
                include_dependencies: true,
              })
              if (!cancelled) next[item.id] = outboundRequestsFromFlow(g.nodes, g.edges)
            } catch {
              if (!cancelled) next[item.id] = []
            }
          }),
        )
      }
      if (!cancelled) {
        setRouteRequests(next)
        setRouteRequestsLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, snapshotId, apisLoading, entryGroups.navigation])

  const loadGraph = useCallback(
    async (
      root: string,
      overrides?: {
        edge_types?: EdgeType[]
        depth?: number
        max_nodes?: number
        view?: 'flow' | 'neighborhood'
      },
    ) => {
      if (!snapshotId) return
      const requestId = ++graphRequest.current
      setLoading(true)
      setError(null)
      try {
        const g = await client.getSubgraph({
          snapshot_id: snapshotId,
          root_id: root,
          direction: 'both',
          edge_types:
            overrides && 'edge_types' in overrides ? overrides.edge_types : edgeTypes,
          depth: overrides?.depth ?? depth,
          max_nodes: overrides?.max_nodes ?? maxNodes,
          view: overrides?.view ?? graphView,
          include_structure: includeStructure,
          include_dependencies: includeDependencies,
        })
        if (requestId !== graphRequest.current) return
        setGraph(g)
        setRootId(g.root_id || root)
        if (g.truncated) announce(t('explorer.announce.truncated'))
      } catch (err) {
        if (requestId !== graphRequest.current) return
        setGraph(null)
        setError(formatError(err, locale))
        announce(formatError(err, locale), true)
      } finally {
        if (requestId === graphRequest.current) setLoading(false)
      }
    },
    [client, snapshotId, edgeTypes, depth, maxNodes, graphView,
     includeStructure, includeDependencies, announce, t, locale],
  )

  const openDetail = async (id: string) => {
    const requestId = ++viewRequest.current
    setSelectedId(id)
    try {
      const d = await client.getEntity(snapshotId, id)
      if (requestId !== viewRequest.current) return
      setDetail(d)
      announce(t('explorer.announce.selected', { name: d.name }))
    } catch (err) {
      if (requestId !== viewRequest.current) return
      setDetail(null)
      announce(formatError(err, locale), true)
    }
  }

  const selectEntity = async (id: string, asRoot = false, graphOverrides?: Parameters<typeof loadGraph>[1]) => {
    const requestId = ++viewRequest.current
    setSelectedId(id)
    setView('graph')
    if (asRoot || !rootId) {
      setOverviewGraph(false)
      setGraphView('flow')
      setRootId(id)
      await loadGraph(id, { ...graphOverrides, view: 'flow' })
    }
    if (requestId !== viewRequest.current) return
    try {
      const d = await client.getEntity(snapshotId, id)
      if (requestId !== viewRequest.current) return
      setDetail(d)
      announce(t('explorer.announce.selected', { name: d.name }))
    } catch (err) {
      if (requestId !== viewRequest.current) return
      setDetail(null)
      announce(formatError(err, locale), true)
    }
  }

  const openProjectOverview = async () => {
    if (!snapshotId) return
    const requestId = ++graphRequest.current
    viewRequest.current += 1
    setActivePreset('')
    setOverviewGraph(true)
    setView('graph')
    setOptionsOpen(false)
    setSelectedId(null)
    setDetail(null)
    setGraph(null)
    setRootId(null)
    setLoading(true)
    setError(null)
    try {
      const graph = await loadProjectOverview(client, snapshotId)
      if (requestId !== graphRequest.current) return
      if (graph.nodes.length === 0) {
        setGraph(null)
        announce(t('explorer.announce.noOverview'), true)
        return
      }
      setGraph(graph)
      if (graph.truncated) announce(t('explorer.announce.truncated'))
      announce(t('explorer.announce.overviewLoaded'))
    } catch (err) {
      if (requestId !== graphRequest.current) return
      setGraph(null)
      setError(formatError(err, locale))
      announce(formatError(err, locale), true)
    } finally {
      if (requestId === graphRequest.current) setLoading(false)
    }
  }

  useEffect(() => {
    if (overviewGraph) return
    if (rootId) void loadGraph(rootId)
  }, [depth, maxNodes, edgeTypes, graphView, includeStructure, includeDependencies, overviewGraph]) // eslint-disable-line react-hooks/exhaustive-deps

  const bumpLayout = () => {
    window.setTimeout(() => setLayoutKey((k) => k + 1), 220)
  }

  const toggleLeft = () => {
    setLeftOpen((v) => !v)
    bumpLayout()
  }
  const toggleRight = () => {
    setRightOpen((v) => !v)
    bumpLayout()
  }
  const focusGraph = () => {
    setLeftOpen(false)
    setRightOpen(false)
    setOptionsOpen(false)
    setAskOpen(false)
    bumpLayout()
    announce(t('explorer.announce.focus'))
  }

  const toggleAsk = () => {
    if (askOpen) {
      setAskOpen(false)
      return
    }
    setAskMounted(true)
    setAskOpen(true)
    setAskEntry(null)
    const token = askOpenToken.current + 1
    askOpenToken.current = token
    void (async () => {
      const path = await openProjectThread()
      if (askOpenToken.current !== token) return
      setAskEntry(path)
      setAskSession((current) => current + 1)
    })()
  }

  const openProjectThread = async () => {
    try {
      let repository = repo
      if (!repository && snapshotId) {
        const list = await client.listRepositories({ limit: 100 })
        for (const item of list.items) {
          const snaps = await client.listSnapshots(item.repository_id, { limit: 50 })
          if (snaps.items.some((snap) => snap.snapshot_id === snapshotId)) {
            repository = item
            break
          }
        }
        repository ??= list.items[0] ?? null
      }
      if (!repository) return '/conversations'
      const page = await client.listConversations({
        repository_id: repository.repository_id,
        limit: 20,
      })
      const current = snapshotId
        ? page.items.find((item) => item.snapshot_id === snapshotId)
        : page.items[0]
      if (current) return `/conversations/${current.conversation_id}`
      const pinned = snapshotId || repository.active_snapshot_id
      if (!pinned) return '/conversations'
      const created = await client.createConversation({
        repository_id: repository.repository_id,
        snapshot_id: pinned,
      })
      return `/conversations/${created.conversation_id}`
    } catch {
      return '/conversations'
    }
  }

  useEffect(() => {
    if (!askOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !event.defaultPrevented) setAskOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [askOpen])

  const openApiFlow = async (id: string) => {
    const entry = apis.find((item) => item.id === id)
    const kind = entry ? endpointEntryKind(entry) : 'other'
    const presetId = flowPresetIdForEntry(kind)
    const preset = GRAPH_PRESETS.find((item) => item.id === presetId)
    if (!preset || !snapshotId) return
    const requestId = ++viewRequest.current
    setSelectedId(id)
    setActivePreset(preset.id)
    setOverviewGraph(false)
    setGraphView('flow')
    setEdgeTypes(preset.edge_types)
    setDepth(preset.max_depth)
    setRootId(id)
    setView('graph')
    setLeftOpen(false)
    await loadGraph(id, {
      edge_types: preset.edge_types,
      depth: preset.max_depth,
      view: 'flow',
    })
    if (requestId !== viewRequest.current) return
    try {
      const d = await client.getEntity(snapshotId, id)
      if (requestId !== viewRequest.current) return
      setDetail(d)
      announce(t('explorer.announce.selected', { name: endpointDisplayLabel(d) }))
    } catch (err) {
      if (requestId !== viewRequest.current) return
      setDetail(null)
      announce(formatError(err, locale), true)
    }
  }

  const applyPreset = (presetId: string) => {
    const preset = GRAPH_PRESETS.find((p) => p.id === presetId)
    if (!preset) return
    if (preset.requiresDataPath && !apiToDbAvailable) return
    setActivePreset(presetId)
    setOverviewGraph(false)
    setGraphView('flow')
    setEdgeTypes(preset.edge_types)
    setDepth(preset.max_depth)
    announce(t('explorer.announce.preset', { label: t(preset.labelKey) }))
    const overrides = {
      edge_types: preset.edge_types, depth: preset.max_depth,
      view: 'flow' as const,
    }
    if (presetId === 'api_to_db') {
      const ep =
        results.find((r) => r.type === 'endpoint' && endpointEntryKind(r) === 'http') ??
        apis.find((r) => endpointEntryKind(r) === 'http') ??
        results.find((r) => r.type === 'endpoint') ??
        results[0]
      if (ep) void selectEntity(ep.id, true, overrides)
    } else if (presetId === 'ui_to_api') {
      const route =
        results.find((r) => r.type === 'endpoint' && endpointEntryKind(r) === 'navigation') ??
        apis.find((r) => endpointEntryKind(r) === 'navigation')
      if (route) void selectEntity(route.id, true, overrides)
    } else if (presetId === 'event_participants' || presetId === 'topic_flow') {
      const topic =
        results.find((r) => r.type === 'topic') ??
        apis.find((r) => endpointEntryKind(r) === 'messaging')
      if (topic) void selectEntity(topic.id, true, overrides)
    } else if (presetId === 'config_users') {
      const cfg = results.find((r) => r.type === 'config')
      if (cfg) void selectEntity(cfg.id, true, overrides)
    } else if (presetId === 'interface_implementations') {
      const iface = results.find((r) => r.type === 'interface')
      if (iface) void selectEntity(iface.id, true, overrides)
    }
  }

  const doExport = async () => {
    if (!snapshotId || (!rootId && !overviewGraph)) return
    setExporting(true)
    setExported(null)
    try {
      if (overviewGraph) {
        const file = await exportProjectOverview(client, snapshotId, repo?.repository_id ?? '')
        setExported({
          schema_version: file.schema_version,
          repository_id: file.repository_id,
          snapshot_id: file.snapshot_id,
          root_id: PROJECT_OVERVIEW_ROOT_ID,
          nodes: file.nodes,
          edges: file.edges,
          diagnostic_summary: [],
          truncated: file.truncated,
          truncation_reasons: file.truncation_reasons,
        })
        announce(
          file.truncated
            ? t('explorer.announce.exportedTrunc')
            : t('explorer.announce.exported'),
        )
        downloadJson(file, `rkg-overview-${shortId(snapshotId, 12)}.json`)
        return
      }
      const ctx = await client.exportContext({
        snapshot_id: snapshotId,
        root_id: rootId!,
        direction: 'both',
        edge_types: edgeTypes ?? [
          'handled_by',
          'calls',
          'depends_on',
          'reads',
          'writes',
          'publishes',
          'consumes',
        ],
        depth,
        max_nodes: maxNodes,
        max_edges: 100,
        max_chars: 20000,
        view: graphView,
        include_structure: includeStructure,
        include_dependencies: includeDependencies,
      })
      setExported(ctx)
      announce(
        ctx.truncated
          ? t('explorer.announce.exportedTrunc')
          : t('explorer.announce.exported'),
      )
      downloadJson(ctx, `rkg-context-${shortId(rootId!, 12)}.json`)
    } catch (err) {
      announce(formatError(err, locale), true)
    } finally {
      setExporting(false)
    }
  }

  const focusId = selectedId ?? rootId
  const graphNodes = useMemo(
    () => new Map((graph?.nodes ?? []).map((node) => [node.id, node])),
    [graph],
  )
  const focusNode = focusId ? graphNodes.get(focusId) ?? null : null
  const relations = useMemo(() => {
    if (!graph || !focusId) return []
    return graph.edges.filter((edge) => edge.source === focusId || edge.target === focusId)
  }, [graph, focusId])
  const sourceEvidence = detail?.evidence?.find((ev) => ev.relative_path)
  const detailFilePath =
    detail?.file_path || sourceEvidence?.relative_path || focusNode?.file_path || null
  // Prefer the entity's own start line (definition site), not the first
  // file-wide evidence row (often line 1 from structure/imports).
  const primaryLocation = (() => {
    const entityLine = detail?.start_line
    if (detailFilePath && entityLine != null && entityLine > 0) {
      return `${detailFilePath}:${entityLine}`
    }
    const linedEvidence =
      detail?.evidence?.find(
        (ev) =>
          ev.relative_path && ev.start_line > 0 && ev.provenance !== 'filesystem',
      ) ??
      detail?.evidence?.find((ev) => ev.relative_path && ev.start_line > 0) ??
      null
    if (linedEvidence) {
      return `${linedEvidence.relative_path}:${linedEvidence.start_line}`
    }
    const nodeLocation = focusNode?.location?.trim()
    if (nodeLocation && /:\d+/.test(nodeLocation)) return nodeLocation
    return null
  })()

  if (!snapshotId) {
    return (
      <div className="page stack-4">
        <header className="page-header">
          <div>
            <h1>{t('explorer.title')}</h1>
            <p>{t('explorer.pickLead')}</p>
          </div>
        </header>
        <div className="empty-state">
          <h2>{t('explorer.noSnapTitle')}</h2>
          <p>{t('explorer.noSnapBody')}</p>
          <div className="row-actions">
            <Button
              variant="primary"
              onClick={() => setParams({ snapshot_id: DEMO_SNAPSHOT_ID })}
            >
              {t('explorer.openDemo')}
            </Button>
            <Button onClick={() => navigate('/repositories')}>{t('explorer.repos')}</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-wide explorer explorer-v2">
      <header className="explorer-top" aria-label={t('explorer.toolbar')}>
        <div className="explorer-identity">
          <span className="explorer-kicker">{t('explorer.title')}</span>
          <strong>
            {repo ? (
              <Link to={`/repositories/${repo.repository_id}`}>{repo.display_name}</Link>
            ) : (
              '…'
            )}
          </strong>
          <span className="mono muted">{shortId(snapshotId, 14)}</span>
          {graph?.truncated ? <Badge tone="warning">{t('explorer.truncated')}</Badge> : null}
        </div>

        <div className="explorer-top-actions">
          <label className="sr-only" htmlFor="preset-select">
            {t('explorer.presetLabel')}
          </label>
          <select
            id="preset-select"
            className="explorer-select"
            value={activePreset}
            onChange={(e) => {
              if (e.target.value) applyPreset(e.target.value)
            }}
          >
            <option value="">{t('explorer.presetPlaceholder')}</option>
            {visiblePresets.map((p) => (
              <option key={p.id} value={p.id}>
                {t(p.labelKey)}
              </option>
            ))}
          </select>

          <button
            type="button"
            className="explorer-tool-btn"
            title={t('explorer.overviewTitle')}
            onClick={() => void openProjectOverview()}
          >
            <LayoutDashboard size={15} aria-hidden />
            {t('explorer.overview')}
          </button>

          <div className="explorer-icon-group" role="group" aria-label={t('explorer.viewMode')}>
            <button
              type="button"
              className={`explorer-tool-btn${view === 'graph' ? ' is-active' : ''}`}
              aria-pressed={view === 'graph'}
              title={t('explorer.graphTitle')}
              onClick={() => setView('graph')}
            >
              <Network size={15} aria-hidden />
              {t('explorer.graph')}
            </button>
            <button
              type="button"
              className={`explorer-tool-btn${view === 'list' ? ' is-active' : ''}`}
              aria-pressed={view === 'list'}
              title={t('explorer.listTitle')}
              onClick={() => setView('list')}
            >
              <List size={15} aria-hidden />
              {t('explorer.list')}
            </button>
            <button
              type="button"
              className={`explorer-tool-btn${view === 'structure' ? ' is-active' : ''}`}
              aria-pressed={view === 'structure'}
              title={t('explorer.structureTitle')}
              onClick={() => setView('structure')}
            >
              <ListTree size={15} aria-hidden />
              {t('explorer.structure')}
            </button>
          </div>

          <div className="explorer-options-wrap">
            <button
              type="button"
              className={`explorer-tool-btn${optionsOpen ? ' is-active' : ''}`}
              aria-expanded={optionsOpen}
              aria-controls="explorer-options"
              title={t('explorer.optionsTitle')}
              onClick={() => setOptionsOpen((v) => !v)}
            >
              <Settings2 size={15} aria-hidden />
              {t('explorer.options')}
            </button>
            {optionsOpen ? (
              <div id="explorer-options" className="explorer-popover" role="dialog">
                <fieldset className="explorer-option-seg">
                  <legend>{t('explorer.graphView')}</legend>
                  <div className="explorer-seg" role="radiogroup" aria-label={t('explorer.graphView')}>
                    <button
                      type="button"
                      role="radio"
                      aria-checked={graphView === 'flow'}
                      onClick={() => {
                        setActivePreset('')
                        setOverviewGraph(false)
                        setGraphView('flow')
                        setEdgeTypes(undefined)
                      }}
                    >
                      {t('explorer.flowView')}
                    </button>
                    <button
                      type="button"
                      role="radio"
                      aria-checked={graphView === 'neighborhood'}
                      onClick={() => {
                        setActivePreset('')
                        setOverviewGraph(false)
                        setGraphView('neighborhood')
                        setEdgeTypes(undefined)
                      }}
                    >
                      {t('explorer.neighborhoodView')}
                    </button>
                  </div>
                </fieldset>
                {graphView === 'flow' ? (
                  <div className="explorer-option-checks">
                    <label className="explorer-check">
                      <input
                        type="checkbox"
                        checked={includeStructure}
                        onChange={(e) => setIncludeStructure(e.target.checked)}
                      />
                      {t('explorer.includeStructure')}
                    </label>
                    <label className="explorer-check">
                      <input
                        type="checkbox"
                        checked={includeDependencies}
                        onChange={(e) => setIncludeDependencies(e.target.checked)}
                      />
                      {t('explorer.includeDependencies')}
                    </label>
                  </div>
                ) : null}
                <div className="explorer-option-pair">
                  <label>
                    {t('explorer.depth')}
                    <input
                      type="number"
                      min={1}
                      max={6}
                      value={depth}
                      onChange={(e) => {
                        setActivePreset('')
                        setDepth(Number(e.target.value) || 1)
                      }}
                    />
                  </label>
                  <label>
                    {t('explorer.maxNodes')}
                    <input
                      type="number"
                      min={5}
                      max={200}
                      value={maxNodes}
                      onChange={(e) => {
                        setActivePreset('')
                        setMaxNodes(Number(e.target.value) || 50)
                      }}
                    />
                  </label>
                </div>
              </div>
            ) : null}
          </div>

          <button
            type="button"
            className="explorer-tool-btn"
            title={t('explorer.focusTitle')}
            onClick={focusGraph}
          >
            <Maximize2 size={15} aria-hidden />
            {t('explorer.focus')}
          </button>

          <button
            type="button"
            className="explorer-tool-btn"
            title={overviewGraph ? t('explorer.exportOverviewTitle') : t('explorer.exportTitle')}
            disabled={!rootId && !overviewGraph}
            onClick={() => {
              setExportOpen(true)
              setExported(null)
            }}
          >
            <Download size={15} aria-hidden />
            {t('explorer.export')}
          </button>

          <button
            type="button"
            className={`explorer-tool-btn${leftOpen ? ' is-active' : ''}`}
            aria-pressed={leftOpen}
            title={leftOpen ? t('explorer.hideResults') : t('explorer.showResults')}
            onClick={toggleLeft}
          >
            <PanelLeft size={15} aria-hidden />
            {t('explorer.results')}
          </button>
          <button
            type="button"
            className={`explorer-tool-btn${rightOpen ? ' is-active' : ''}`}
            aria-pressed={rightOpen}
            title={rightOpen ? t('explorer.hideDetail') : t('explorer.showDetail')}
            onClick={toggleRight}
          >
            <PanelRight size={15} aria-hidden />
            {t('explorer.detail')}
          </button>
          <button
            type="button"
            className={`explorer-tool-btn${askOpen ? ' is-active' : ''}`}
            aria-pressed={askOpen}
            aria-controls="explorer-ask"
            title={t('explorer.askTitle')}
            onClick={toggleAsk}
          >
            <MessageSquare size={15} aria-hidden />
            {t('explorer.ask')}
          </button>
        </div>
      </header>

      {error ? (
        <div className="state-block error" role="alert" style={{ margin: 16 }}>
          <h2>{t('explorer.errorTitle')}</h2>
          <p>{error}</p>
          <Button
            onClick={() =>
              navigate(repo ? `/repositories/${repo.repository_id}` : '/repositories')
            }
          >
            {t('explorer.backRepo')}
          </Button>
        </div>
      ) : null}

      <div className="explorer-stage">
        {!leftOpen ? (
          <button
            type="button"
            className="explorer-edge-toggle is-left"
            onClick={toggleLeft}
            title={t('explorer.showSearch')}
          >
            <ChevronRight size={16} aria-hidden />
          </button>
        ) : null}

        <AnimatePresence initial={false}>
          {leftOpen ? (
            <motion.aside
              key="left"
              className="explorer-panel explorer-panel-left"
              aria-label={t('explorer.searchPanel')}
              initial={panelMotion.left.initial}
              animate={panelMotion.left.animate}
              exit={panelMotion.left.exit}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <div className="explorer-panel-inner">
                <div className="explorer-panel-head">
                  <h2>{t('explorer.results')}</h2>
                  <button
                    type="button"
                    className="explorer-icon-btn"
                    aria-label={t('explorer.collapseSearch')}
                    onClick={toggleLeft}
                  >
                    <ChevronLeft size={16} />
                  </button>
                </div>

                <form
                  className="explorer-search"
                  onSubmit={(e) => {
                    e.preventDefault()
                    void runSearch()
                  }}
                  role="search"
                >
                  <Search size={15} aria-hidden />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={t('explorer.searchPlaceholder')}
                    aria-label={t('explorer.searchAria')}
                  />
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    aria-label={t('explorer.typeFilter')}
                  >
                    <option value="">{t('explorer.typeAll')}</option>
                    <option value="endpoint">{t('explorer.type.endpoint')}</option>
                    <option value="function">{t('explorer.type.function')}</option>
                    <option value="class">{t('explorer.type.class')}</option>
                    <option value="directory">{t('explorer.type.directory')}</option>
                    <option value="file">{t('explorer.type.file')}</option>
                    <option value="module">{t('explorer.type.module')}</option>
                    <option value="table">{t('explorer.type.table')}</option>
                    <option value="topic">{t('explorer.type.topic')}</option>
                    <option value="config">{t('explorer.type.config')}</option>
                    <option value="interface">{t('explorer.type.interface')}</option>
                    <option value="dependency">{t('explorer.type.dependency')}</option>
                  </select>
                </form>

                <p className="explorer-result-count muted">
                  {searchLoading
                    ? t('explorer.searching')
                    : t('explorer.resultCount', { n: results.length })}
                </p>

                <div className="explorer-result-scroll">
                  {results.length === 0 ? (
                    <p className="muted explorer-empty-hint">
                      {query ? t('explorer.noMatch') : t('explorer.noEntities')}
                    </p>
                  ) : (
                    <ul className="entity-list">
                      {results.map((e) => (
                        <li key={e.id}>
                          <button
                            type="button"
                            className="entity-item"
                            aria-selected={selectedId === e.id}
                            onClick={() => void selectEntity(e.id, true)}
                          >
                            <Badge>{e.type}</Badge>
                            <span className="name">{e.name}</span>
                            <span className="qn">{e.qualified_name}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </motion.aside>
          ) : null}
        </AnimatePresence>

        <section
          className="explorer-canvas"
          aria-label={view === 'structure' ? t('explorer.structureTree') : t('explorer.canvas')}
        >
          {view === 'structure' ? (
            <SnapshotStructure
              snapshotId={snapshotId}
              schemaVersion={snapshotSchema}
              selectedId={selectedId}
              onSelectLeaf={(id) => void openDetail(id)}
            />
          ) : view === 'list' ? (
            <div className="explorer-list-fallback">
              <h2 className="section-title">
                {uiOnlyCatalog
                  ? t('explorer.apiListUi')
                  : messagingOnlyCatalog
                    ? t('explorer.apiListMessaging')
                    : t('explorer.apiList')}
              </h2>
              <p className="muted" style={{ margin: '0 0 12px' }}>
                {uiOnlyCatalog
                  ? t('explorer.apiListHintUi')
                  : messagingOnlyCatalog
                    ? t('explorer.apiListHintMessaging')
                    : t('explorer.apiListHint')}
              </p>
              {showEntryTabs ? (
                <div className="row-actions" style={{ marginBottom: 12 }} role="tablist" aria-label={t('explorer.apiList')}>
                  {(
                    [
                      ['all', 'explorer.entryFilterAll'],
                      ['http', 'explorer.entryFilterApi'],
                      ['navigation', 'explorer.entryFilterRoutes'],
                      ['messaging', 'explorer.entryFilterTopics'],
                    ] as const
                  )
                    .filter(([value]) => {
                      if (value === 'all') return true
                      if (value === 'http') return entryGroups.http.length > 0
                      if (value === 'navigation') return entryGroups.navigation.length > 0
                      return entryGroups.messaging.length > 0
                    })
                    .map(([value, labelKey]) => (
                    <Button
                      key={value}
                      variant={entryFilter === value ? 'primary' : 'secondary'}
                      aria-pressed={entryFilter === value}
                      onClick={() => setEntryFilter(value)}
                    >
                      {t(labelKey)}
                    </Button>
                  ))}
                </div>
              ) : null}
              {apisLoading ? (
                <p className="muted">{t('explorer.apiListLoading')}</p>
              ) : visibleEntries.length === 0 ? (
                <p className="muted">
                  {uiOnlyCatalog
                    ? t('explorer.apiListEmptyUi')
                    : messagingOnlyCatalog
                      ? t('explorer.apiListEmptyMessaging')
                      : t('explorer.apiListEmpty')}
                </p>
              ) : (
                <ul className="entity-list">
                  {visibleEntries.map((api) => {
                    const kind = endpointEntryKind(api)
                    const kindLabel =
                      kind === 'navigation'
                        ? t('explorer.entryKind.navigation')
                        : kind === 'http'
                          ? t('explorer.entryKind.http')
                          : kind === 'messaging'
                            ? t('explorer.entryKind.messaging')
                            : api.type
                    const page = routePageHandler(api)
                    const signal = routeSignal(api)
                    const requests =
                      kind === 'navigation'
                        ? routeOutboundRequests(api).length > 0
                          ? routeOutboundRequests(api)
                          : (routeRequests[api.id] ?? [])
                        : []
                    const resolvingNav =
                      kind === 'navigation' &&
                      routeOutboundRequests(api).length === 0 &&
                      routeRequestsLoading &&
                      !(api.id in routeRequests)
                    const secondary =
                      kind === 'navigation'
                        ? resolvingNav
                          ? t('explorer.outboundRequestsLoading')
                          : requests.length === 0
                            ? signal === 'shell'
                              ? t('explorer.routeSignal.shell')
                              : signal === 'partial'
                                ? t('explorer.routeSignal.partial')
                                : page
                                  ? `${page} · ${t('explorer.outboundRequestsEmpty')}`
                                  : t('explorer.outboundRequestsEmpty')
                            : page ?? t('explorer.outboundRequests')
                        : kind === 'http'
                          ? t('explorer.flowKind.http')
                          : kind === 'messaging'
                            ? t('explorer.flowKind.messaging')
                            : api.qualified_name
                    return (
                      <li key={api.id}>
                        <button
                          type="button"
                          className="entity-item"
                          aria-selected={selectedId === api.id}
                          onClick={() => void openApiFlow(api.id)}
                        >
                          <Badge>{kindLabel}</Badge>
                          <span className="name">{endpointDisplayLabel(api)}</span>
                          <span className="qn">{secondary}</span>
                          {kind === 'navigation' && requests.length > 0 ? (
                            <span className="outbound-requests" role="list">
                              {requests.map((line) => (
                                <span key={line} className="outbound-request" role="listitem">
                                  → {line}
                                </span>
                              ))}
                            </span>
                          ) : null}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          ) : graph && (rootId || overviewGraph) ? (
            <ReactFlowProvider>
              {rootId &&
              detail &&
              isPartialUiFlow(
                endpointEntryKind(detail),
                graph.nodes,
                graph.edges,
              ) ? (
                <p className="muted" role="status" style={{ margin: '0 0 8px', padding: '0 12px' }}>
                  {t('explorer.partialUiFlow')}
                </p>
              ) : null}
              <KnowledgeGraph
                nodes={graph.nodes}
                edges={graph.edges}
                rootId={overviewGraph ? PROJECT_OVERVIEW_ROOT_ID : rootId!}
                selectedId={selectedId}
                mode={overviewGraph ? 'architecture' : 'flow'}
                showStructure={includeStructure}
                focusOnly={graphView === 'flow' ? false : focusOnly}
                layoutKey={layoutKey}
                onSelect={(id) => void selectEntity(id)}
              />
            </ReactFlowProvider>
          ) : loading && (rootId || overviewGraph) ? (
            <div className="explorer-canvas-empty" aria-busy="true">
              <h2>{t('explorer.loadingGraph')}</h2>
            </div>
          ) : (
            <div className="explorer-canvas-empty">
              <h2>{t('explorer.pickEntityTitle')}</h2>
              <p>{t('explorer.pickEntityBody')}</p>
              <div className="row-actions">
                <Button variant="primary" onClick={() => void openProjectOverview()}>
                  {t('explorer.projectOverview')}
                </Button>
                {!leftOpen ? (
                  <Button onClick={toggleLeft}>{t('explorer.openSearch')}</Button>
                ) : null}
              </div>
            </div>
          )}
        </section>

        <AnimatePresence initial={false}>
          {rightOpen ? (
            <motion.aside
              key="right"
              className="explorer-panel explorer-panel-right"
              aria-label={t('explorer.detailPanel')}
              initial={panelMotion.right.initial}
              animate={panelMotion.right.animate}
              exit={panelMotion.right.exit}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <div className="explorer-panel-inner">
                <div className="explorer-panel-head">
                  <h2>{t('explorer.detail')}</h2>
                  <button
                    type="button"
                    className="explorer-icon-btn"
                    aria-label={t('explorer.collapseDetail')}
                    onClick={toggleRight}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>

                <div className="drawer-body stack-3">
                  {detail ? (
                    <>
                      <div>
                        <Badge>
                          {endpointEntryKind(detail) === 'navigation'
                            ? t('explorer.detailBadge.navigation')
                            : endpointEntryKind(detail) === 'http'
                              ? t('explorer.detailBadge.http')
                              : endpointEntryKind(detail) === 'messaging'
                                ? t('explorer.detailBadge.messaging')
                                : detail.type}
                        </Badge>
                        {endpointEntryKind(detail) !== 'other' ? (
                          <Badge>
                            {endpointEntryKind(detail) === 'navigation'
                              ? t('explorer.flowKind.navigation')
                              : endpointEntryKind(detail) === 'messaging'
                                ? t('explorer.flowKind.messaging')
                                : t('explorer.flowKind.http')}
                          </Badge>
                        ) : null}
                        {endpointEntryKind(detail) === 'navigation' &&
                        routeSignal(detail) === 'outbound_http' ? (
                          <Badge>{t('explorer.routeSignal.outbound_http')}</Badge>
                        ) : null}
                        {endpointEntryKind(detail) === 'navigation' &&
                        routeSignal(detail) === 'shell' ? (
                          <Badge>{t('explorer.routeSignal.shell')}</Badge>
                        ) : null}
                        {endpointEntryKind(detail) === 'navigation' &&
                        routeSignal(detail) === 'partial' ? (
                          <Badge>{t('explorer.routeSignal.partial')}</Badge>
                        ) : null}
                        <h2 className="section-title" style={{ marginTop: 8 }}>
                          {endpointDisplayLabel(detail)}
                        </h2>
                        <p className="mono muted">{detail.qualified_name}</p>
                        {detailFilePath ? (
                          <p className="mono muted" title={detailFilePath}>
                            {t('explorer.file')}: {detailFilePath}
                          </p>
                        ) : null}
                        {primaryLocation ? (
                          <p className="mono muted" title={primaryLocation}>
                            {t('explorer.evidence')}: {primaryLocation}
                          </p>
                        ) : null}
                        {detail.summary ? <p>{detail.summary}</p> : null}
                        {endpointEntryKind(detail) === 'navigation' ? (
                          <div className="outbound-requests-block">
                            <h3 className="detail-block-title">{t('explorer.outboundRequests')}</h3>
                            {(() => {
                              const fromAttrs = routeOutboundRequests(detail)
                              const fromLazy = routeRequests[detail.id] ?? []
                              const fromGraph =
                                graph && graph.root_id === detail.id
                                  ? outboundRequestsFromFlow(graph.nodes, graph.edges)
                                  : []
                              const lines =
                                fromAttrs.length > 0
                                  ? fromAttrs
                                  : fromGraph.length > 0
                                    ? fromGraph
                                    : fromLazy
                              const responses =
                                fromAttrs.length > 0
                                  ? routeOutboundResponses(detail)
                                  : graph && graph.root_id === detail.id
                                    ? outboundResponsesFromFlow(graph.nodes)
                                    : []
                              if (lines.length === 0) {
                                return (
                                  <p className="muted">{t('explorer.outboundRequestsEmpty')}</p>
                                )
                              }
                              return (
                                <ul className="outbound-requests-detail">
                                  {lines.map((line, index) => {
                                    const response = responses[index]
                                    return (
                                      <li key={line} className="mono">
                                        <div>→ {line}</div>
                                        {response ? (
                                          <div className="muted">
                                            → {t('explorer.outboundResponse')}: {response}
                                          </div>
                                        ) : null}
                                      </li>
                                    )
                                  })}
                                </ul>
                              )
                            })()}
                          </div>
                        ) : null}
                      </div>
                      <div>
                        <h3 className="detail-block-title">{t('explorer.metadata')}</h3>
                        <dl className="detail-meta">
                          {Object.entries(detail.metadata)
                            .filter(([k]) => k !== 'registration_chain')
                            .map(([k, v]) => (
                              <div key={k}>
                                <dt className="muted">{k}</dt>
                                <dd>{v}</dd>
                              </div>
                            ))}
                        </dl>
                      </div>
                      {focusNode ? (
                        <section className="graph-relations-panel detail-relations" aria-label={t('explorer.relations')}>
                          <div className="graph-relations-header">
                            <div>
                              <strong>{t('explorer.relations')}</strong>
                              <span className="graph-relations-count">{relations.length}</span>
                            </div>
                            <button
                              type="button"
                              className="graph-relations-toggle"
                              onClick={() => setFocusOnly((value) => !value)}
                            >
                              {focusOnly ? t('explorer.relationsAll') : t('explorer.relationsFocused')}
                            </button>
                          </div>
                          <p className="graph-relations-entity" title={focusNode.qualified_name}>
                            {focusNode.label}
                          </p>
                          {relations.length ? (
                            <ul className="graph-relations-list">
                              {relations.map((edge) => {
                                const outgoing = edge.source === focusId
                                const otherId = outgoing ? edge.target : edge.source
                                const other = graphNodes.get(otherId)
                                return (
                                  <li key={edge.id}>
                                    <button type="button" onClick={() => void selectEntity(other?.id ?? otherId)}>
                                      <span className="graph-relation-type" style={{ borderColor: relationAccent(edge.type) }}>
                                        {outgoing ? '→' : '←'} {edge.label || edge.type}
                                      </span>
                                      <span className="graph-relation-name" title={other?.qualified_name}>
                                        {other?.label ?? otherId}
                                      </span>
                                    </button>
                                  </li>
                                )
                              })}
                            </ul>
                          ) : (
                            <p className="graph-relations-empty">{t('explorer.relationsEmpty')}</p>
                          )}
                        </section>
                      ) : null}
                    </>
                  ) : (
                    <p className="muted">{t('explorer.pickNode')}</p>
                  )}
                </div>
              </div>
            </motion.aside>
          ) : null}
        </AnimatePresence>

        {!rightOpen ? (
          <button
            type="button"
            className="explorer-edge-toggle is-right"
            onClick={toggleRight}
            title={t('explorer.showDetailEdge')}
          >
            <ChevronLeft size={16} aria-hidden />
          </button>
        ) : null}
      </div>

      {exportOpen ? (
        <div
          className="dialog-backdrop"
          role="presentation"
          onClick={() => setExportOpen(false)}
        >
          <div
            className="dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="export-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <h2 id="export-title">{t('explorer.exportTitleDialog')}</h2>
              <Button
                variant="ghost"
                aria-label={t('common.close')}
                onClick={() => setExportOpen(false)}
              >
                <X size={16} />
              </Button>
            </div>
            <p>
              {overviewGraph
                ? t('explorer.exportOverviewBody')
                : t('explorer.exportBody', {
                    root: rootId ?? '',
                    depth,
                    max: maxNodes,
                  })}
            </p>
            {exported ? (
              <p>
                {exported.truncated ? (
                  <Badge tone="warning">
                    {t('explorer.exportTruncated', {
                      reasons: exported.truncation_reasons.join(', '),
                    })}
                  </Badge>
                ) : (
                  <Badge tone="success">{t('explorer.exportComplete')}</Badge>
                )}
              </p>
            ) : null}
            <div className="dialog-actions">
              <Button onClick={() => setExportOpen(false)}>{t('common.cancel')}</Button>
              <Button
                variant="primary"
                disabled={exporting || (!rootId && !overviewGraph)}
                onClick={() => void doExport()}
              >
                {exporting ? t('explorer.exporting') : t('explorer.downloadJson')}
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {askMounted ? (
        <div
          id="explorer-ask"
          className={`explorer-ask${askOpen ? '' : ' is-closed'}`}
          role="dialog"
          aria-modal="false"
          aria-hidden={!askOpen}
          aria-label={t('explorer.askPanel')}
        >
          <div className="explorer-ask-head">
            <h2>{t('explorer.askPanel')}</h2>
            <button
              type="button"
              className="explorer-icon-btn"
              aria-label={t('common.close')}
              onClick={() => setAskOpen(false)}
            >
              <X size={16} />
            </button>
          </div>
          <div
            className="explorer-ask-body"
            onClickCapture={(event) => {
              const anchor = (event.target as HTMLElement).closest('a')
              const href = anchor?.getAttribute('href') ?? ''
              if (!href.startsWith('/') || href.startsWith('/conversations')) return
              event.preventDefault()
              event.stopPropagation()
              setAskOpen(false)
              navigate(href)
            }}
          >
            <AskHistory key={askSession} initialPath={askEntry ?? '/conversations'}>
              {askEntry ? (
                <Routes>
                  <Route path="/conversations" element={<ConversationsPage />} />
                  <Route path="/conversations/:conversationId" element={<ConversationPage />} />
                  <Route path="*" element={<Navigate to={askEntry} replace />} />
                </Routes>
              ) : (
                <p className="ask-status explorer-ask-loading">{t('common.loading')}</p>
              )}
            </AskHistory>
          </div>
        </div>
      ) : null}
    </div>
  )
}

const ASK_ROUTE_CONTEXT = {
  outlet: null,
  matches: [],
  isDataRoute: false,
}

function AskHistory({
  initialPath,
  children,
}: {
  initialPath: string
  children: React.ReactNode
}) {
  const historyRef = useRef<ReturnType<typeof UNSAFE_createMemoryHistory> | null>(null)
  if (historyRef.current == null) {
    historyRef.current = UNSAFE_createMemoryHistory({
      initialEntries: [initialPath],
      v5Compat: true,
    })
  }
  const history = historyRef.current
  const [entry, setEntry] = useState({
    action: history.action,
    location: history.location,
  })

  useLayoutEffect(
    () =>
      history.listen((next) => {
        setEntry({ action: next.action, location: next.location })
      }),
    [history],
  )

  const navigation = useMemo(
    () => ({
      basename: '/',
      navigator: history,
      static: false,
      useTransitions: undefined,
      future: {},
    }),
    [history],
  )
  const location = useMemo(
    () => ({ location: entry.location, navigationType: entry.action }),
    [entry.action, entry.location],
  )

  return (
    <UNSAFE_NavigationContext.Provider value={navigation}>
      <UNSAFE_LocationContext.Provider value={location}>
        <UNSAFE_RouteContext.Provider value={ASK_ROUTE_CONTEXT}>{children}</UNSAFE_RouteContext.Provider>
      </UNSAFE_LocationContext.Provider>
    </UNSAFE_NavigationContext.Provider>
  )
}
