import { ChevronLeft, MessageSquare, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useLocale } from '../../i18n'
import { formatError, relativeTime } from '../../lib/format'
import type { ConversationSummary, Repository } from '../../types/api'
import { RkgApiError } from '../../types/api'

export function ConversationsPage() {
  const client = getRkgClient()
  const navigate = useNavigate()
  const location = useLocation()
  const returnId =
    (location.state as { conversationId?: string; repositoryId?: string } | null)?.conversationId ??
    ''
  const hintedRepositoryId =
    (location.state as { repositoryId?: string } | null)?.repositoryId ?? ''
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const headingRef = useRef<HTMLHeadingElement>(null)
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [repositoryId, setRepositoryId] = useState('')
  const [items, setItems] = useState<ConversationSummary[]>([])
  const [previews, setPreviews] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<ConversationSummary | null>(null)
  const [deleting, setDeleting] = useState(false)

  const selected = repositories.find((item) => item.repository_id === repositoryId) ?? null

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const repos = await client.listRepositories({ limit: 100 })
      setRepositories(repos.items)
      const chosen =
        repositoryId && repos.items.some((item) => item.repository_id === repositoryId)
          ? repositoryId
          : hintedRepositoryId &&
              repos.items.some((item) => item.repository_id === hintedRepositoryId)
            ? hintedRepositoryId
            : (repos.items[0]?.repository_id ?? '')
      setRepositoryId(chosen)
      if (!chosen) {
        setItems([])
        setPreviews({})
        return
      }
      const page = await client.listConversations({ repository_id: chosen, limit: 20 })
      const labels = await Promise.all(
        page.items.map(async (item) => {
          try {
            const history = await client.getConversation(item.conversation_id, { limit: 1 })
            const first = [...history.turns.items].sort((a, b) => a.sequence - b.sequence)[0]
            return [item.conversation_id, previewText(first?.question ?? '')] as const
          } catch {
            return [item.conversation_id, ''] as const
          }
        }),
      )
      setItems(page.items)
      setPreviews(Object.fromEntries(labels))
      announce(t('ask.title'))
    } catch (err) {
      const message = formatError(err, locale)
      setError(message)
      announce(message, true)
    } finally {
      setLoading(false)
    }
  }, [announce, client, hintedRepositoryId, locale, repositoryId, t])

  useEffect(() => {
    void load()
  }, [load])

  const confirmDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true)
    try {
      await client.deleteConversation(pendingDelete.conversation_id)
      announce(t('ask.deleted'))
      setPendingDelete(null)
      await load()
      queueMicrotask(() => headingRef.current?.focus())
    } catch (err) {
      const message =
        err instanceof RkgApiError && err.code === 'conversation_busy'
          ? t('ask.busy')
          : formatError(err, locale)
      setError(message)
      setPendingDelete(null)
      announce(message, true)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="page ask-screen">
      <header className="ask-top">
        {returnId ? (
          <Link className="ask-back" to={`/conversations/${returnId}`} aria-label={t('common.back')} title={t('common.back')}>
            <ChevronLeft size={16} aria-hidden />
          </Link>
        ) : null}
        <div className="ask-top-copy">
          <h1 tabIndex={-1} ref={headingRef}>
            {t('ask.title')}
          </h1>
          <p>{t('ask.lead')}</p>
        </div>
      </header>

      {error ? (
        <p className="error ask-banner" role="alert">
          {error}
        </p>
      ) : null}

      <div className="ask-stream">
        {loading ? <p className="ask-status">{t('common.loading')}</p> : null}

        {!loading && repositories.length === 0 ? (
          <div className="empty-state ask-empty">
            <MessageSquare size={22} aria-hidden />
            <h2>{t('ask.noRepository')}</h2>
            <Button variant="primary" onClick={() => navigate('/repositories/new')}>
              {t('repo.list.add')}
            </Button>
          </div>
        ) : null}

        {!loading && selected && !selected.active_snapshot_id ? (
          <div className="empty-state ask-empty">
            <h2>{t('ask.noSnapshotTitle')}</h2>
            <p>{t('ask.noSnapshotBody')}</p>
            <Button variant="primary" onClick={() => navigate(`/repositories/${selected.repository_id}`)}>
              {t('ask.indexFirst')}
            </Button>
          </div>
        ) : null}

        {!loading && selected?.active_snapshot_id && items.length === 0 ? (
          <div className="empty-state ask-empty">
            <h2>{t('ask.emptyTitle')}</h2>
            <p>{t('ask.emptyBody')}</p>
          </div>
        ) : null}

        {items.length > 0 ? (
          <ul className="ask-list">
            {items.map((item) => {
              const when = relativeTime(item.updated_at, locale)
              const label = previews[item.conversation_id] || item.title.trim() || when
              return (
                <li key={item.conversation_id} className="ask-list-item">
                  <Link to={`/conversations/${item.conversation_id}`} title={label}>
                    {label}
                  </Link>
                  <p className="ask-list-meta">
                    <span>{when}</span>
                  </p>
                  <Button
                    variant="ghost"
                    className="ask-delete"
                    aria-label={t('ask.deleteAria', { name: label })}
                    title={t('common.delete')}
                    onClick={() => setPendingDelete(item)}
                  >
                    <Trash2 size={14} aria-hidden />
                  </Button>
                </li>
              )
            })}
          </ul>
        ) : null}
      </div>

      <ConfirmDialog
        open={pendingDelete != null}
        title={t('ask.deleteTitle')}
        danger
        confirmLabel={deleting ? t('common.loading') : t('common.delete')}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setPendingDelete(null)}
      >
        <p>{t('ask.deleteBody')}</p>
      </ConfirmDialog>
    </div>
  )
}

function previewText(question: string): string {
  return question.replace(/\s+/g, ' ').trim()
}
