import {
  AlertTriangle,
  Network,
  Pencil,
  Play,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useLocale } from '../../i18n'
import { formatError, relativeTime, shortId } from '../../lib/format'
import type { Repository, Snapshot, TechnologyDetection } from '../../types/api'
import { RkgApiError } from '../../types/api'

type PendingAction =
  | { kind: 'activate'; snap: Snapshot }
  | { kind: 'delete-snapshot'; snap: Snapshot }
  | { kind: 'delete-repo' }
  | null

export function RepositoryDetailPage() {
  const { repositoryId = '' } = useParams()
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const headingRef = useRef<HTMLHeadingElement>(null)

  const [repo, setRepo] = useState<Repository | null>(null)
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [tech, setTech] = useState<TechnologyDetection[]>([])
  const [techLoading, setTechLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [indexing, setIndexing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [blockedMessage, setBlockedMessage] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingAction>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [r, snaps] = await Promise.all([
        client.getRepository(repositoryId),
        client.listSnapshots(repositoryId),
      ])
      setRepo(r)
      setSnapshots(snaps.items)
    } catch (err) {
      setError(formatError(err, locale))
    } finally {
      setLoading(false)
    }
  }, [client, repositoryId, locale])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const snapshotId = repo?.active_snapshot_id
    if (!snapshotId) {
      setTech([])
      setTechLoading(false)
      return
    }
    let cancelled = false
    setTechLoading(true)
    void (async () => {
      try {
        const items = await client.listTechnologies(snapshotId)
        if (!cancelled) setTech(items)
      } catch {
        if (!cancelled) setTech([])
      } finally {
        if (!cancelled) setTechLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, repo?.active_snapshot_id])

  const startIndex = async () => {
    if (!repo) return
    setIndexing(true)
    setActionError(null)
    try {
      const job = await client.startIndexJob(repo.repository_id)
      announce(t('repo.detail.indexStarted'))
      navigate(`/jobs/${job.job_id}`)
    } catch (err) {
      if (err instanceof RkgApiError && err.code === 'index_job_busy') {
        setActionError(err.message)
        announce(err.message, true)
      } else {
        setActionError(formatError(err, locale))
        announce(formatError(err, locale), true)
      }
    } finally {
      setIndexing(false)
    }
  }

  const runPending = async () => {
    if (!pending || !repo) return
    setBusy(true)
    setActionError(null)
    setBlockedMessage(null)
    try {
      if (pending.kind === 'activate') {
        const updated = await client.activateSnapshot(
          repositoryId,
          pending.snap.snapshot_id,
        )
        setRepo(updated)
        announce(t('repo.detail.activated', { id: shortId(pending.snap.snapshot_id) }))
        setPending(null)
        navigate(
          `/explorer?snapshot_id=${encodeURIComponent(pending.snap.snapshot_id)}`,
        )
        return
      }
      if (pending.kind === 'delete-snapshot') {
        await client.deleteSnapshot(repositoryId, pending.snap.snapshot_id)
        announce(t('repo.detail.snapDeleted', { id: shortId(pending.snap.snapshot_id) }))
        setPending(null)
        await load()
        queueMicrotask(() => headingRef.current?.focus())
        return
      }
      if (pending.kind === 'delete-repo') {
        await client.deleteRepository(repositoryId)
        announce(t('repo.detail.repoDeleted', { name: repo.display_name }))
        setPending(null)
        navigate('/repositories')
      }
    } catch (err) {
      const message = formatError(err, locale)
      const code = err instanceof RkgApiError ? err.code : ''
      if (
        code === 'snapshot_active' ||
        code === 'snapshot_in_use' ||
        code === 'repository_busy' ||
        code === 'repository_in_use'
      ) {
        setBlockedMessage(message)
        setPending(null)
        announce(message, true)
      } else {
        setActionError(message)
        setPending(null)
        announce(message, true)
      }
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="page repo-mgmt">
        <div className="state-block" aria-busy="true">
          <h2>{t('repo.detail.loading')}</h2>
        </div>
      </div>
    )
  }

  if (error || !repo) {
    return (
      <div className="page repo-mgmt">
        <div className="state-block error" role="alert">
          <h2>{t('repo.detail.unavailable')}</h2>
          <p>{error ?? t('common.notFound')}</p>
          <Button onClick={() => navigate('/repositories')}>{t('repo.create.backList')}</Button>
        </div>
      </div>
    )
  }

  const confirmTitle =
    pending?.kind === 'activate'
      ? t('repo.detail.activateTitle')
      : pending?.kind === 'delete-snapshot'
        ? t('repo.detail.deleteSnapTitle')
        : pending?.kind === 'delete-repo'
          ? t('repo.detail.deleteRepoTitle')
          : ''

  const confirmDanger =
    pending?.kind === 'delete-snapshot' || pending?.kind === 'delete-repo'

  const visibleTech = tech.filter((item) => item.support_state !== 'detected_only')

  return (
    <div className="page repo-mgmt stack-6">
      <header className="page-header">
        <div>
          <h1 tabIndex={-1} ref={headingRef}>
            {repo.display_name}
          </h1>
          <p>
            <code className="mono">{repo.source_locator_redacted}</code>
            {' · '}
            rev {repo.revision}
          </p>
        </div>
        <div className="row-actions">
          <Button onClick={() => void load()} aria-label={t('common.refresh')}>
            <RefreshCw size={16} aria-hidden />
            {t('repo.detail.refresh')}
          </Button>
          <Button onClick={() => navigate(`/repositories/${repo.repository_id}/edit`)}>
            <Pencil size={16} aria-hidden />
            {t('repo.detail.editDefaults')}
          </Button>
          {repo.active_snapshot_id ? (
            <Button
              variant="primary"
              onClick={() =>
                navigate(
                  `/explorer?snapshot_id=${encodeURIComponent(repo.active_snapshot_id!)}`,
                )
              }
            >
              <Network size={16} aria-hidden />
              {t('repo.detail.openExplorer')}
            </Button>
          ) : (
            <Button variant="primary" disabled={indexing} onClick={() => void startIndex()}>
              <Play size={16} aria-hidden />
              {indexing ? t('repo.detail.starting') : t('repo.detail.index')}
            </Button>
          )}
        </div>
      </header>

      {!repo.active_snapshot_id ? (
        <motion.div
          className="hint-card"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <AlertTriangle size={18} aria-hidden />
          <div>
            <strong>{t('repo.detail.noActiveTitle')}</strong>
            <p>{t('repo.detail.noActiveBody')}</p>
          </div>
        </motion.div>
      ) : null}

      {actionError ? (
        <div className="state-block error repo-alert" role="alert" style={{ padding: 16 }}>
          <p>{actionError}</p>
        </div>
      ) : null}

      {blockedMessage ? (
        <div className="state-block error repo-alert is-blocked" role="alert" style={{ padding: 16 }}>
          <strong>{t('repo.detail.blocked')}</strong>
          <p>{blockedMessage}</p>
          <Button onClick={() => setBlockedMessage(null)}>{t('common.close')}</Button>
        </div>
      ) : null}

      <section className="panel panel-pad stack-3 repo-status">
        <h2 className="section-title">{t('repo.detail.status')}</h2>
        <div className="chip-row">
          {repo.active_snapshot_id ? (
            <Badge tone="success">
              {t('repo.detail.activeSnap', { id: shortId(repo.active_snapshot_id, 14) })}
            </Badge>
          ) : (
            <Badge tone="warning">{t('repo.detail.noActiveTitle')}</Badge>
          )}
          <Badge>source · {repo.source_type}</Badge>
          {repo.app_module ? (
            <Badge>
              app · <span className="mono">{repo.app_module}:{repo.app_symbol}</span>
            </Badge>
          ) : null}
        </div>
        <div className="row-actions">
          <Button disabled={indexing} onClick={() => void startIndex()}>
            <Play size={16} aria-hidden />
            {repo.active_snapshot_id ? t('repo.detail.reindex') : t('repo.detail.index')}
          </Button>
          <span className="muted repo-inline-hint">{t('repo.detail.reindexHint')}</span>
        </div>
      </section>

      <section className="stack-3">
        <h2 className="section-title">{t('repo.detail.snapHistory')}</h2>
        {snapshots.length === 0 ? (
          <div className="empty-state">
            <h2>{t('repo.detail.noSnapsTitle')}</h2>
            <p>{t('repo.detail.noSnapsBody')}</p>
          </div>
        ) : (
          <div className="panel repo-table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">{t('repo.detail.colSnapshot')}</th>
                  <th scope="col">{t('repo.detail.colCreated')}</th>
                  <th scope="col">{t('repo.detail.colEntities')}</th>
                  <th scope="col">{t('repo.detail.colStatus')}</th>
                  <th scope="col">
                    <span className="sr-only">{t('repo.detail.colActions')}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {snapshots.map((snap) => (
                  <tr key={snap.snapshot_id}>
                    <td data-label={t('repo.detail.colSnapshot')}>
                      <code className="mono">{shortId(snap.snapshot_id, 16)}</code>
                      <div className="muted" style={{ fontSize: 12 }}>
                        {shortId(snap.source_revision.replace(/^manifest:/, ''), 12)}
                      </div>
                    </td>
                    <td data-label={t('repo.detail.colCreated')}>
                      {relativeTime(snap.created_at, locale)}
                    </td>
                    <td data-label={t('repo.detail.colEntities')}>
                      {t('repo.detail.metrics', {
                        entities: snap.metrics.entity_count,
                        edges: snap.metrics.edge_count,
                      })}
                      {snap.metrics.warning_count > 0
                        ? t('repo.detail.metricsWarn', { n: snap.metrics.warning_count })
                        : ''}
                    </td>
                    <td data-label={t('repo.detail.colStatus')}>
                      {snap.status === 'unavailable' ? (
                        <Badge tone="error">{t('repo.detail.unavailableBadge')}</Badge>
                      ) : snap.is_active ? (
                        <Badge tone="success">{t('repo.detail.activeBadge')}</Badge>
                      ) : (
                        <Badge>{t('repo.detail.inactiveBadge')}</Badge>
                      )}
                    </td>
                    <td data-label={t('repo.detail.colActions')}>
                      <div className="row-actions">
                        <Button
                          variant={snap.is_active ? 'primary' : 'secondary'}
                          disabled={snap.status === 'unavailable'}
                          onClick={() =>
                            navigate(
                              `/explorer?snapshot_id=${encodeURIComponent(snap.snapshot_id)}`,
                            )
                          }
                        >
                          {t('common.open')}
                        </Button>
                        {!snap.is_active && snap.status !== 'unavailable' ? (
                          <Button
                            onClick={() => setPending({ kind: 'activate', snap })}
                          >
                            {t('repo.detail.activate')}
                          </Button>
                        ) : null}
                        <Button
                          variant="danger"
                          aria-label={t('repo.detail.deleteSnapAria', {
                            id: shortId(snap.snapshot_id),
                          })}
                          onClick={() => setPending({ kind: 'delete-snapshot', snap })}
                        >
                          <Trash2 size={14} aria-hidden />
                          {t('common.delete')}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel panel-pad stack-3" aria-label={t('repo.detail.tech')}>
        <h2 className="section-title">{t('repo.detail.tech')}</h2>
        <p className="muted" style={{ margin: 0 }}>
          {t('repo.detail.techHint')}
        </p>
        {!repo.active_snapshot_id ? (
          <p className="muted">{t('repo.detail.techNoSnapshot')}</p>
        ) : techLoading ? (
          <p className="muted">{t('repo.detail.techLoading')}</p>
        ) : visibleTech.length === 0 ? (
          <p className="muted">{t('repo.detail.techEmpty')}</p>
        ) : (
          <ul className="repo-tech-list">
            {visibleTech.map((item) => (
              <li key={item.technology}>{item.technology}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel panel-pad stack-3 danger-zone" aria-labelledby="danger-heading">
        <h2 id="danger-heading" className="section-title">
          {t('repo.detail.dangerTitle')}
        </h2>
        <p className="muted">{t('repo.detail.dangerBody')}</p>
        <Button variant="danger" onClick={() => setPending({ kind: 'delete-repo' })}>
          <Trash2 size={16} aria-hidden />
          {t('repo.detail.deleteRepo')}
        </Button>
      </section>

      <p className="muted">
        <Link to="/repositories">{t('repo.detail.allRepos')}</Link>
      </p>

      <ConfirmDialog
        open={pending !== null}
        title={confirmTitle}
        danger={confirmDanger}
        confirmLabel={
          pending?.kind === 'activate'
            ? t('repo.detail.activateConfirm')
            : pending?.kind === 'delete-snapshot'
              ? t('repo.detail.deleteSnapConfirm')
              : t('repo.detail.deleteRepo')
        }
        onCancel={() => setPending(null)}
        onConfirm={() => {
          if (!busy) void runPending()
        }}
      >
        {pending?.kind === 'activate' ? (
          <p>
            {t('repo.detail.activateBody', {
              id: shortId(pending.snap.snapshot_id, 16),
              when: relativeTime(pending.snap.created_at, locale),
            })}
          </p>
        ) : null}
        {pending?.kind === 'delete-snapshot' ? (
          <p>
            {t('repo.detail.deleteSnapBody', {
              id: shortId(pending.snap.snapshot_id, 16),
            })}
          </p>
        ) : null}
        {pending?.kind === 'delete-repo' ? (
          <p>{t('repo.detail.deleteRepoBody', { name: repo.display_name })}</p>
        ) : null}
      </ConfirmDialog>
    </div>
  )
}
