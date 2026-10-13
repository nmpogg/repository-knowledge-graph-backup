import { Info, Plus, RefreshCw, Search, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useAnnouncer } from '../../components/ui/Announcer'
import { useLocale } from '../../i18n'
import { formatError, relativeTime, shortId } from '../../lib/format'
import type { Repository } from '../../types/api'
import { RkgApiError } from '../../types/api'

export function RepositoryListPage() {
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const offset = Number(params.get('offset') ?? '0') || 0
  const headingRef = useRef<HTMLHeadingElement>(null)

  const [items, setItems] = useState<Repository[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState(q)
  const [pendingDelete, setPendingDelete] = useState<Repository | null>(null)
  const [blockedMessage, setBlockedMessage] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadGen = useRef(0)

  const load = useCallback(async () => {
    const gen = ++loadGen.current
    setLoading(true)
    setError(null)
    try {
      const page = await client.listRepositories({ q: q || undefined, offset, limit: 20 })
      if (gen !== loadGen.current) return
      setItems(page.items)
      setTotal(page.page.total)
      announce(t('repo.list.announceCount', { total: page.page.total }))
    } catch (err) {
      if (gen !== loadGen.current) return
      setError(formatError(err, locale))
      announce(formatError(err, locale), true)
    } finally {
      if (gen === loadGen.current) setLoading(false)
    }
  }, [client, q, offset, announce, t, locale])

  useEffect(() => {
    void load()
    return () => {
      loadGen.current += 1
    }
  }, [load])

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const next = new URLSearchParams(params)
    if (query.trim()) next.set('q', query.trim())
    else next.delete('q')
    next.delete('offset')
    setParams(next)
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true)
    setBlockedMessage(null)
    try {
      await client.deleteRepository(pendingDelete.repository_id)
      announce(t('repo.list.deleted', { name: pendingDelete.display_name }))
      setPendingDelete(null)
      await load()
      queueMicrotask(() => headingRef.current?.focus())
    } catch (err) {
      const message = formatError(err, locale)
      if (
        err instanceof RkgApiError &&
        (err.code === 'repository_busy' || err.code === 'repository_in_use')
      ) {
        setBlockedMessage(message)
        setPendingDelete(null)
        announce(message, true)
      } else {
        setError(message)
        setPendingDelete(null)
        announce(message, true)
      }
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="page repo-mgmt stack-6">
      <header className="page-header">
        <div>
          <h1 tabIndex={-1} ref={headingRef}>
            {t('repo.list.title')}
          </h1>
          <p>{t('repo.list.lead')}</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/repositories/new')}>
          <Plus size={16} aria-hidden />
          {t('repo.list.add')}
        </Button>
      </header>

      <motion.div
        className="hint-card"
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22 }}
      >
        <Info size={18} aria-hidden />
        <div>
          <strong>{t('repo.list.hintTitle')}</strong>
          <p>{t('repo.list.hintBody')}</p>
        </div>
      </motion.div>

      <form className="toolbar repo-toolbar" onSubmit={onSearch} role="search">
        <div className="field" style={{ flex: 1, minWidth: 200 }}>
          <label htmlFor="repo-q" className="sr-only">
            {t('repo.list.searchLabel')}
          </label>
          <input
            id="repo-q"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('repo.list.searchPlaceholder')}
          />
        </div>
        <Button type="submit">
          <Search size={16} aria-hidden />
          {t('repo.list.search')}
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={() => void load()}
          aria-label={t('common.refresh')}
        >
          <RefreshCw size={16} aria-hidden />
        </Button>
        <span className="muted">{t('repo.list.total', { total })}</span>
      </form>

      {blockedMessage ? (
        <div className="state-block error repo-alert is-blocked" role="alert" style={{ padding: 16 }}>
          <strong>{t('repo.list.cannotDelete')}</strong>
          <p>{blockedMessage}</p>
          <Button onClick={() => setBlockedMessage(null)}>{t('common.close')}</Button>
        </div>
      ) : null}

      {loading ? (
        <div className="state-block" aria-busy="true">
          <h2>{t('repo.list.loadingTitle')}</h2>
          <p>{t('repo.list.loadingBody')}</p>
        </div>
      ) : error ? (
        <div className="state-block error" role="alert">
          <h2>{t('repo.list.loadErrorTitle')}</h2>
          <p>{error}</p>
          <Button variant="primary" onClick={() => void load()}>
            {t('common.retry')}
          </Button>
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <h2>{q ? t('repo.list.emptySearchTitle') : t('repo.list.emptyTitle')}</h2>
          <p>{q ? t('repo.list.emptySearchBody') : t('repo.list.emptyBody')}</p>
          {q ? (
            <Button
              onClick={() => {
                setQuery('')
                setParams({})
              }}
            >
              {t('repo.list.clearSearch')}
            </Button>
          ) : (
            <Button variant="primary" onClick={() => navigate('/repositories/new')}>
              {t('repo.list.add')}
            </Button>
          )}
        </div>
      ) : (
        <div className="panel repo-table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{t('repo.list.colName')}</th>
                <th scope="col">{t('repo.list.colSource')}</th>
                <th scope="col">{t('repo.list.colActive')}</th>
                <th scope="col">{t('repo.list.colUpdated')}</th>
                <th scope="col">
                  <span className="sr-only">{t('repo.list.colActions')}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((repo) => (
                <tr key={repo.repository_id}>
                  <td data-label={t('repo.list.colName')}>
                    <Link to={`/repositories/${repo.repository_id}`}>
                      <strong>{repo.display_name}</strong>
                    </Link>
                  </td>
                  <td data-label={t('repo.list.colSource')}>
                    <code className="mono">{repo.source_locator_redacted}</code>
                  </td>
                  <td data-label={t('repo.list.colActive')}>
                    {repo.active_snapshot_id ? (
                      <Badge tone="success">
                        {t('repo.list.activeBadge', { id: shortId(repo.active_snapshot_id) })}
                      </Badge>
                    ) : (
                      <Badge>{t('repo.list.noActive')}</Badge>
                    )}
                  </td>
                  <td data-label={t('repo.list.colUpdated')}>
                    {relativeTime(repo.updated_at, locale)}
                  </td>
                  <td data-label={t('repo.list.colActions')}>
                    <div className="row-actions">
                      <Button
                        onClick={() => navigate(`/repositories/${repo.repository_id}`)}
                      >
                        {t('common.open')}
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
                          Explorer
                        </Button>
                      ) : null}
                      <Button
                        variant="danger"
                        aria-label={t('repo.list.deleteAria', { name: repo.display_name })}
                        onClick={() => setPendingDelete(repo)}
                      >
                        <Trash2 size={14} aria-hidden />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        title={t('repo.list.deleteTitle')}
        danger
        confirmLabel={deleting ? t('repo.list.deleting') : t('repo.list.deleteConfirm')}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!deleting) void confirmDelete()
        }}
      >
        {pendingDelete ? (
          <p>
            {t('repo.list.deleteBody', {
              name: pendingDelete.display_name,
              locator: pendingDelete.source_locator_redacted,
            })}
          </p>
        ) : null}
      </ConfirmDialog>
    </div>
  )
}
