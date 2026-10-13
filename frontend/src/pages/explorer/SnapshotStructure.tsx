import { ChevronDown, Expand, ZoomIn, ZoomOut } from 'lucide-react'
import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { getRkgClient } from '../../client'
import { Button } from '../../components/ui/Button'
import { useLocale, type MessageKey } from '../../i18n'
import { formatError } from '../../lib/format'
import type { EntityType } from '../../types/api'
import { RkgApiError } from '../../types/api'
import {
  buildStructureTree,
  collectSnapshotEntities,
  defaultExpandedKeys,
  type StructureNode,
} from './structureTree'
import './snapshotStructure.css'

/** Keep in sync with `[data-family]` rules in snapshotStructure.css. */
const FAMILY_COUNT = 6
const MIN_ZOOM = 0.2
const MAX_ZOOM = 1.75

function clampZoom(value: number) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(value * 100) / 100))
}

function fitZoom(view: HTMLElement, forest: HTMLElement): number | null {
  const previousZoom = forest.style.getPropertyValue('--structure-zoom')
  forest.style.setProperty('--structure-zoom', '1')
  const width = forest.scrollWidth
  const height = forest.scrollHeight
  if (previousZoom) forest.style.setProperty('--structure-zoom', previousZoom)
  else forest.style.removeProperty('--structure-zoom')
  if (width < 1 || height < 1) return null
  return clampZoom(
    Math.min(
      (Math.max(view.clientWidth, 1) - 48) / width,
      (Math.max(view.clientHeight, 1) - 48) / height,
      1,
    ),
  )
}

const TYPE_LABEL: Record<EntityType, MessageKey> = {
  directory: 'explorer.type.directory',
  file: 'explorer.type.file',
  module: 'explorer.type.module',
  class: 'explorer.type.class',
  function: 'explorer.type.function',
  endpoint: 'explorer.type.endpoint',
  table: 'explorer.type.table',
  topic: 'explorer.type.topic',
  config: 'explorer.type.config',
  interface: 'explorer.type.interface',
  dependency: 'explorer.type.dependency',
}

function SegmentLabel({ text, mono }: { text: string; mono: boolean }) {
  const parts = text.split(/([.:])/g)
  return (
    <span className={mono ? 'structure-label mono' : 'structure-label'}>
      {parts.map((part, index) =>
        part === '.' || part === ':' ? (
          <span key={`${part}-${index}`}>
            {part}
            <wbr />
          </span>
        ) : (
          <span key={`${part}-${index}`}>{part}</span>
        ),
      )}
    </span>
  )
}

interface StructureTreeProps {
  snapshotId: string
  schemaVersion?: string
  selectedId: string | null
  onSelectLeaf: (entityId: string) => void
}

type LoadPhase = 'loading' | 'empty' | 'error' | 'ready'

export function SnapshotStructure({ snapshotId, schemaVersion, selectedId, onSelectLeaf }: StructureTreeProps) {
  const client = getRkgClient()
  const { t, locale } = useLocale()
  const [phase, setPhase] = useState<LoadPhase>('loading')
  const [error, setError] = useState<string | null>(null)
  const [roots, setRoots] = useState<StructureNode[]>([])
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set())
  const [focusKey, setFocusKey] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)
  const [zoom, setZoom] = useState(1)
  const forestRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const fittedSnapshot = useRef<string | null>(null)

  useLayoutEffect(() => {
    if (phase !== 'ready' || fittedSnapshot.current === snapshotId) return
    const view = viewportRef.current
    const forest = forestRef.current
    if (!view || !forest) return
    if (view.clientWidth < 64 || view.clientHeight < 64) return
    const next = fitZoom(view, forest)
    if (next === null) return
    fittedSnapshot.current = snapshotId
    setZoom(next)
  }, [roots, phase, snapshotId])

  useEffect(() => {
    const view = viewportRef.current
    if (!view || phase !== 'ready') return
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) return
      event.preventDefault()
      const step = event.deltaY < 0 ? 0.1 : -0.1
      setZoom((current) => clampZoom(current + step))
    }
    view.addEventListener('wheel', onWheel, { passive: false })
    return () => view.removeEventListener('wheel', onWheel)
  }, [phase])

  useEffect(() => {
    let cancelled = false
    setPhase('loading')
    setError(null)
    ;(async () => {
      try {
        const entities = await collectSnapshotEntities((params) =>
          client.searchEntities(snapshotId, params),
        )
        if (cancelled) return
        const forest = buildStructureTree(entities, schemaVersion)
        const open = defaultExpandedKeys(forest)
        setRoots(forest)
        setExpanded(new Set(open))
        setFocusKey(forest[0]?.key ?? null)
        setPhase(forest.length === 0 ? 'empty' : 'ready')
      } catch (err) {
        if (cancelled) return
        const message =
          err instanceof RkgApiError && err.code === 'snapshot_unavailable'
            ? err.message
            : formatError(err, locale)
        setRoots([])
        setError(message)
        setPhase('error')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, snapshotId, schemaVersion, locale, reloadToken])

  if (phase === 'loading') {
    return (
      <div className="explorer-canvas-empty" aria-busy="true">
        <h2 role="status">{t('explorer.structureLoading')}</h2>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="explorer-canvas-empty">
        <div className="state-block error" role="alert">
          <h2>{t('explorer.errorTitle')}</h2>
          <p>{error}</p>
          <Button onClick={() => setReloadToken((value) => value + 1)}>{t('common.retry')}</Button>
        </div>
      </div>
    )
  }

  if (phase === 'empty') {
    return (
      <div className="explorer-canvas-empty">
        <h2>{t('explorer.structureEmpty')}</h2>
      </div>
    )
  }

  const toggle = (key: string) => {
    setExpanded((current) => {
      const next = new Set(current)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const onTreeKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target
    if (!(target instanceof HTMLElement) || target.getAttribute('role') !== 'treeitem') return
    const items = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>('[role="treeitem"]'),
    )
    const index = items.indexOf(target)
    if (index < 0) return
    const key = target.dataset.nodeKey
    const isOpen = target.dataset.expanded === 'true'
    const collapsible = target.dataset.collapsible === 'true'

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      items[Math.min(index + 1, items.length - 1)]?.focus()
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      items[Math.max(index - 1, 0)]?.focus()
      return
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault()
      if (collapsible && !isOpen && key) toggle(key)
      else items[index + 1]?.focus()
      return
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      if (collapsible && isOpen && key) {
        toggle(key)
        return
      }
      const parentKey = target.dataset.parentKey
      if (!parentKey) return
      const parent = Array.from(
        event.currentTarget.querySelectorAll<HTMLElement>('[data-node-key]'),
      ).find((element) => element.dataset.nodeKey === parentKey)
      parent?.focus()
    }
  }

  const boxProps = (key: string) => ({
    type: 'button' as const,
    'data-node-key': key,
    tabIndex: focusKey === key ? 0 : -1,
    onFocus: () => setFocusKey(key),
  })

  const renderNodes = (
    nodes: StructureNode[],
    parentKey: string,
    familyOffset: number | null,
  ): ReactNode =>
    nodes.map((node, index) => {
      const family =
        familyOffset === null ? undefined : String((familyOffset + index) % FAMILY_COUNT)
      if (node.kind === 'leaf') {
        const name = node.entity.name
        const typeLabel = t(TYPE_LABEL[node.entity.type])
        const accessible =
          name === node.label ? `${node.label}, ${typeLabel}` : `${name}, ${node.label}, ${typeLabel}`
        return (
          <li
            key={node.key}
            className="structure-node"
            role="none"
            data-family={family}
          >
            <span className="structure-stem" aria-hidden="true" />
            <button
              {...boxProps(node.key)}
              role="treeitem"
              className="structure-box"
              data-parent-key={parentKey}
              aria-selected={selectedId === node.entity.id}
              aria-label={accessible}
              onClick={() => onSelectLeaf(node.entity.id)}
            >
              <span className="structure-cap" aria-hidden="true" />
              <SegmentLabel text={node.label} mono />
              {name !== node.label ? <span className="structure-hint">{name}</span> : null}
              <span className="structure-hint">{typeLabel}</span>
            </button>
          </li>
        )
      }

      const open = expanded.has(node.key)
      return (
        <li
          key={node.key}
          className="structure-node"
          role="none"
          data-family={family}
        >
          <span className="structure-stem" aria-hidden="true" />
          <button
            {...boxProps(node.key)}
            role="treeitem"
            className={parentKey === '' ? 'structure-box structure-box-root' : 'structure-box'}
            data-parent-key={parentKey}
            data-collapsible="true"
            data-expanded={open ? 'true' : 'false'}
            aria-expanded={open}
            aria-selected={node.entity ? selectedId === node.entity.id : undefined}
            aria-label={node.entity ? `${node.label}, ${t(TYPE_LABEL[node.entity.type])}` : undefined}
            onClick={() => {
              toggle(node.key)
              if (node.entity) onSelectLeaf(node.entity.id)
            }}
          >
            <span className="structure-cap" aria-hidden="true" />
            <ChevronDown
              size={14}
              aria-hidden
              className={`structure-chevron${open ? ' is-open' : ''}`}
            />
            <SegmentLabel text={node.label} mono />
            {node.entity ? <span className="structure-hint">{t(TYPE_LABEL[node.entity.type])}</span> : null}
          </button>
          {open ? (
            <ul className="structure-children" role="group">
              {renderNodes(node.children, node.key, null)}
            </ul>
          ) : null}
        </li>
      )
    })

  return (
    <div className="explorer-structure">
      <div className="structure-zoom" role="group" aria-label={t('explorer.structureZoom')}>
        <Button
          variant="ghost"
          aria-label={t('explorer.structureZoomOut')}
          onClick={() => setZoom((current) => clampZoom(current - 0.1))}
        >
          <ZoomOut size={16} aria-hidden />
        </Button>
        <button
          type="button"
          className="structure-zoom-level"
          aria-label={t('explorer.structureZoomReset')}
          onClick={() => setZoom(1)}
        >
          {Math.round(zoom * 100)}%
        </button>
        <Button
          variant="ghost"
          aria-label={t('explorer.structureZoomIn')}
          onClick={() => setZoom((current) => clampZoom(current + 0.1))}
        >
          <ZoomIn size={16} aria-hidden />
        </Button>
        <Button
          variant="ghost"
          aria-label={t('explorer.structureZoomFit')}
          onClick={() => {
            const view = viewportRef.current
            const forest = forestRef.current
            if (!view || !forest) return
            const next = fitZoom(view, forest)
            if (next !== null) setZoom(next)
          }}
        >
          <Expand size={16} aria-hidden />
        </Button>
      </div>
      <div
        className="structure-scroll"
        role="tree"
        aria-label={t('explorer.structureTree')}
        onKeyDown={onTreeKeyDown}
        ref={viewportRef}
      >
      <div
        className="structure-forest"
        role="none"
        ref={forestRef}
        style={{ ['--structure-zoom' as string]: String(zoom) }}
      >
        <div className="structure-chart" role="none">
          <ul className="structure-children structure-roots" role="group">
            {renderNodes(roots, '', 0)}
          </ul>
        </div>
      </div>
      </div>
    </div>
  )
}
