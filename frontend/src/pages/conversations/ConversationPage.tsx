import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { Ellipsis, MessageSquare, Plus, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useLocale, type Locale, type TranslateFn } from '../../i18n'
import { formatError, relativeTime, shortId } from '../../lib/format'
import type {
  Citation,
  ConversationTurn,
  ExactCitation,
  EntitySummary,
  Repository,
  Snapshot,
  TurnSubmitResult,
} from '../../types/api'
import { RkgApiError } from '../../types/api'
import { TurnReply } from './TurnReply'

export function ConversationPage() {
  const { conversationId = '' } = useParams()
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const headingRef = useRef<HTMLHeadingElement>(null)
  const streamRef = useRef<HTMLDivElement>(null)
  const [repository, setRepository] = useState<Repository | null>(null)
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [revision, setRevision] = useState(1)
  const [pinnedSnapshot, setPinnedSnapshot] = useState('')
  const [focusId, setFocusId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [candidates, setCandidates] = useState<EntitySummary[]>([])
  const [question, setQuestion] = useState('')
  const [legacy, setLegacy] = useState(false)
  const [capabilitiesReady, setCapabilitiesReady] = useState(false)
  const [historyReady, setHistoryReady] = useState(false)
  const [providerEnabled, setProviderEnabled] = useState(true)
  const submitRequest = useRef(0)
  const sourceRequest = useRef(0)
  const loadRequest = useRef(0)
  const [evidenceLoading, setEvidenceLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [unavailable, setUnavailable] = useState(false)
  const [conflict, setConflict] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [providerOff, setProviderOff] = useState(false)
  const [citation, setCitation] = useState<Citation | null>(null)
  const [evidence, setEvidence] = useState<ExactCitation | null>(null)
  const [evidenceError, setEvidenceError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [starting, setStarting] = useState(false)

  const load = useCallback(async () => {
    const ticket = ++loadRequest.current
    setLoading(true)
    setHistoryReady(false)
    setCapabilitiesReady(false)
    try {
      let legacyMode = false
      try {
        const capabilities = await client.getConversationCapabilities()
        if (ticket !== loadRequest.current) return
        const required = ['ui_locale','response_metadata_v1','exact_citation_lookup','history_unavailable']
        if (capabilities.schema_version !== 'rkg.conversation-capabilities/1' || !required.every((feature) => capabilities.features.includes(feature))) throw new RkgApiError(502,'invalid_capabilities','Invalid capabilities.')
        setProviderEnabled(capabilities.provider_enabled)
        if (!capabilities.provider_enabled) setProviderOff(true)
      } catch (err) {
        if (ticket !== loadRequest.current) return
        if (err instanceof RkgApiError && err.status === 404) { legacyMode = true; setProviderEnabled(true) }
        else throw err
      }
      setLegacy(legacyMode)
      setCapabilitiesReady(true)
      const history = await client.getConversation(conversationId, { limit: 100, ...(!legacyMode ? { include_unavailable: true } : {}) })
      if (ticket !== loadRequest.current) return
      setRevision(history.conversation.revision)
      setPinnedSnapshot(history.conversation.snapshot_id)
      setFocusId(history.conversation.focus_entity_id)
      setTitle(history.conversation.title)
      setTurns(history.turns.items)
      const available = history.snapshot_available !== false
      setCandidates(available ? history.candidate_entities : [])
      setUnavailable(!available)
      const repo = await client.getRepository(history.conversation.repository_id)
      if (ticket !== loadRequest.current) return
      setRepository(repo)
      if (available) {
        const snap = await client.getSnapshot(history.conversation.repository_id, history.conversation.snapshot_id)
        if (ticket !== loadRequest.current) return
        setSnapshot(snap)
      } else setSnapshot(null)
      setHistoryReady(true)
    } catch (err) {
      if (ticket !== loadRequest.current) return
      if (err instanceof RkgApiError && err.code === 'snapshot_unavailable') {
        setUnavailable(true)
        setError(t('ask.snapshotUnavailable'))
        announce(t('ask.snapshotUnavailable'), true)
      } else {
        const message = formatError(err, locale)
        setError(message)
        announce(message, true)
      }
    } finally {
      if (ticket === loadRequest.current) setLoading(false)
    }
  }, [announce, client, conversationId, locale, t])

  useEffect(() => {
    void load()
    return () => { loadRequest.current += 1; sourceRequest.current += 1 }
  }, [load])

  useEffect(() => {
    setCitation(null)
    setEvidence(null)
    setHistoryReady(false)
    setCandidates([])
    setTurns([])
    setRevision(1)
    setFocusId(null)
    setPinnedSnapshot('')
    setTitle('')
    setRepository(null)
    setSnapshot(null)
    setError(null)
    setProviderOff(false)
    setPending(false)
    setQuestion('')
    setNotice(null)
    setConflict(false)
    return () => { submitRequest.current += 1 }
  }, [conversationId])

  useEffect(() => {
    const node = streamRef.current
    if (!node) return
    node.scrollTop = node.scrollHeight
  }, [turns, pending, candidates])

  const applyResult = (result: TurnSubmitResult) => {
    setRevision(result.revision)
    setCandidates(result.candidate_entities)
    setQuestion('')
    setConflict(false)
    setProviderOff(false)
  }

  const submit = async (text: string, rootId?: string) => {
    const trimmed = text.trim()
    if (!trimmed || pending || loading || !historyReady || unavailable || !capabilitiesReady || !providerEnabled) return
    const ticket = ++submitRequest.current
    setPending(true)
    setError(null)
    setNotice(null)
    announce(t('ask.pending'))
    try {
      const result = await client.submitTurn(conversationId, {
        question: text,
        client_request_id: crypto.randomUUID(),
        expected_revision: revision,
        root_id: rootId,
        ...(!legacy ? { ui_locale: locale } : {}),      })
      if (ticket !== submitRequest.current) return
      applyResult(result)
      if (result.status === 'answered') announce(result.answer || t('ask.send'))
      if (result.status === 'needs_clarification') announce(t('ask.clarification'))
      if (result.status === 'insufficient_evidence') announce(t('ask.insufficient'))
      if (result.history_truncated) announce(t('ask.historyTruncated'))
      await load()
    } catch (err) {
      if (ticket !== submitRequest.current) return
      if (err instanceof RkgApiError && err.code === 'conversation_conflict') {
        setConflict(true)
        setNotice(t('ask.conflict'))
        announce(t('ask.conflict'), true)
        return
      }
      if (err instanceof RkgApiError && err.code === 'snapshot_unavailable') {
        setUnavailable(true)
        setError(t('ask.snapshotUnavailable'))
        announce(t('ask.snapshotUnavailable'), true)
        return
      }
      const message = messageFor(err, t, locale)
      setProviderOff(err instanceof RkgApiError && (err.code === 'llm_disabled' || err.status === 503))
      setError(message)
      setNotice(t('ask.draftKept'))
      announce(message, true)
      if (err instanceof RkgApiError && [502, 503, 504].includes(err.status)) {
        await load()
      }
    } finally {
      if (ticket === submitRequest.current) setPending(false)
    }
  }

  const openCitation = async (turn: ConversationTurn, index: number) => {
    const item = turn.citations[index]
    const ticket = ++sourceRequest.current
    setCitation(item)
    setEvidence(null)
    setEvidenceError(null)
    setEvidenceLoading(true)
    if (unavailable || legacy || !item?.evidence_id || item.snapshot_id !== pinnedSnapshot) {
      setEvidenceError(t('ask.citationUnavailable'))
      setEvidenceLoading(false)
      return
    }
    try {
      const detail = await client.getExactCitation(conversationId, turn.turn_id, index)
      if (ticket !== sourceRequest.current) return
      const location = detail.evidence
      const safe = location && location.id === item.evidence_id && detail.snapshot_id === pinnedSnapshot &&
        detail.conversation_id === conversationId && detail.turn_id === turn.turn_id && detail.citation_index === index &&
        detail.schema_version === 'rkg.citation/1' && typeof location.file_path === 'string' && location.file_path.length > 0 && location.file_path.length <= 2000 && !location.file_path.includes(':') &&
        !/^(?:\/|[A-Za-z]:)/.test(location.file_path) && !location.file_path.includes('\\') &&
        !location.file_path.split('/').some((part) => part === '..' || part === '.') &&
        !/[\u0000-\u001f]/.test(location.file_path) &&
        (location.provenance === 'filesystem' ? location.start_line === null && location.end_line === null :
          location.provenance === 'source' && Number.isInteger(location.start_line) && Number.isInteger(location.end_line) &&
          (location.start_line ?? 0) > 0 && (location.end_line ?? 0) >= (location.start_line ?? 0))
      if (!safe) throw new RkgApiError(404,'not_found','Citation unavailable.')
      setEvidence(detail)
    } catch (err) {
      if (ticket !== sourceRequest.current) return
      if (err instanceof RkgApiError && err.code === 'snapshot_unavailable') setUnavailable(true)
      setEvidenceError(err instanceof RkgApiError && err.status === 401 ? formatError(err, locale) : t('ask.citationUnavailable'))
    } finally {
      if (ticket === sourceRequest.current) setEvidenceLoading(false)
    }
  }

  const remove = async () => {
    try {
      await client.deleteConversation(conversationId)
      announce(t('ask.deleted'))
      navigate('/conversations')
    } catch (err) {
      const message =
        err instanceof RkgApiError && err.code === 'conversation_busy'
          ? t('ask.busy')
          : formatError(err, locale)
      setError(message)
      setConfirmDelete(false)
      announce(message, true)
    }
  }

  const activeDiffers =
    repository?.active_snapshot_id &&
    pinnedSnapshot &&
    repository.active_snapshot_id !== pinnedSnapshot
  const busy = pending || turns.some((item) => item.status === 'pending')
  const name = title.trim()
  const heading = name || repository?.display_name || t('ask.title')

  const startNew = async () => {
    if (!repository || starting || pending || unavailable) return
    setStarting(true)
    setError(null)
    try {
      const created = await client.createConversation({
        repository_id: repository.repository_id,
        snapshot_id: pinnedSnapshot || undefined,
      })
      navigate(`/conversations/${created.conversation_id}`)
    } catch (err) {
      const message = formatError(err, locale)
      setError(message)
      announce(message, true)
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="page ask-screen">
      <header className="ask-top">
        <div className="ask-top-copy">
          <h1 tabIndex={-1} ref={headingRef}>
            {heading}
          </h1>
          <section className="ask-context" aria-label={t('ask.context')}>
            {name && repository?.display_name ? <span>{repository.display_name}</span> : null}
            <span>{t('ask.pinned', { id: shortId(pinnedSnapshot || snapshot?.snapshot_id || '', 14) })}</span>
            {snapshot ? <span>{relativeTime(snapshot.created_at, locale)}</span> : null}
            <span>{t('ask.warnings', { n: snapshot?.metrics.warning_count ?? 0 })}</span>
            <span>{focusId ? `${t('ask.focus')} ${shortId(focusId, 18)}` : t('ask.noFocus')}</span>
          </section>
        </div>
        <div className="ask-top-actions">
          <button
            type="button"
            className="ask-back"
            aria-label={t('ask.new')}
            title={t('ask.new')}
            disabled={!repository || starting || pending || unavailable || loading}
            onClick={() => void startNew()}
          >
            <Plus size={16} aria-hidden />
          </button>
          <Link
            className="ask-back"
            to="/conversations"
            state={{ conversationId, repositoryId: repository?.repository_id ?? '' }}
            aria-label={t('ask.back')}
            title={t('ask.back')}
          >
            <Ellipsis size={16} aria-hidden />
          </Link>
          <Button
            variant="ghost"
            className="ask-delete"
            disabled={busy}
            aria-label={name ? t('ask.deleteAria', { name }) : t('common.delete')}
            title={t('common.delete')}
            onClick={() => setConfirmDelete(true)}
          >
            <Trash2 size={14} aria-hidden />
          </Button>
        </div>
      </header>

      {activeDiffers ? (
        <p className="ask-note">
          {t('ask.activeDiffers', {
            pinned: shortId(pinnedSnapshot, 14),
            active: shortId(repository?.active_snapshot_id ?? '', 14),
          })}{' '}
          <button
            type="button"
            className="linkish"
            onClick={() =>
              void client
                .createConversation({ repository_id: repository?.repository_id ?? '' })
                .then((created) => navigate(`/conversations/${created.conversation_id}`))
            }
          >
            {t('ask.startOnActive')}
          </button>
        </p>
      ) : null}

      {error ? (
        <p className="error ask-banner" role="alert">
          {error}
        </p>
      ) : null}
      {!loading && !capabilitiesReady ? <Button onClick={() => { setError(null); void load() }}>{t('ask.reload')}</Button> : null}
      {legacy ? <p className="ask-note">{t('ask.legacyMode')}</p> : null}
      {!providerEnabled ? <p className="ask-note">{t('ask.disabled')}</p> : null}
      {notice ? <p className="ask-note">{notice}</p> : null}
      {conflict ? (
        <p className="ask-note">
          <Button
            onClick={() => {
              setConflict(false)
              void load()
            }}
          >
            {t('ask.reload')}
          </Button>
        </p>
      ) : null}
      {unavailable ? (
        <p className="ask-note">
          <Link to={repository ? `/repositories/${repository.repository_id}` : '/repositories'}>
            {t('ask.reindex')}
          </Link>
        </p>
      ) : null}

      <div className="ask-stream" ref={streamRef}>
        {loading ? <p className="ask-status">{t('common.loading')}</p> : null}
        {pending ? (
          <p className="ask-status" role="status">
            {t('ask.pending')}
          </p>
        ) : null}

        {!loading && turns.length === 0 ? (
          <div className="ask-thread-empty">
            <MessageSquare size={22} aria-hidden />
            <p>{t('ask.questionPlaceholder')}</p>
          </div>
        ) : null}

        <ol className="ask-thread">
          {turns.map((turn) => <li key={turn.turn_id} className="ask-turn">
            <p className="ask-bubble is-user">{turn.question}</p>
            <TurnReply turn={turn} t={t} unavailable={unavailable} legacy={legacy} onSource={(selected, index) => void openCitation(selected, index)} />
          </li>)}
        </ol>
      </div>

      {candidates.length > 0 ? (
        <div className="ask-candidates">
          <h2>{t('ask.clarification')}</h2>
          {candidates.map((item, index) => (
            <Button
              key={item.id}
              disabled={busy || loading || !historyReady || unavailable || !capabilitiesReady || !providerEnabled}
              aria-label={t('ask.chooseCandidate', {
                n: index + 1,
                type: item.type,
                name: item.qualified_name,
              })}
              onClick={() => void submit(String(index + 1), item.id)}
            >
              {t('ask.chooseCandidate', {
                n: index + 1,
                type: item.type,
                name: item.qualified_name,
              })} {item.attributes?.method} {item.attributes?.path}
            </Button>
          ))}
        </div>
      ) : null}

      <form
        className="ask-composer"
        onSubmit={(event) => {
          event.preventDefault()
          void submit(question)
        }}
      >
        <div className="field ask-field">
          <label htmlFor="ask-question">{t('ask.questionLabel')}</label>
          <textarea
            id="ask-question"
            rows={2}
            value={question}
            disabled={unavailable || loading}
            placeholder={t('ask.questionPlaceholder')}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <p className="hint">{t('ask.characters', { n: question.length })}</p>
        </div>
        <Button variant="primary" type="submit" disabled={busy || unavailable || loading || !historyReady || !question.trim() || !capabilitiesReady || !providerEnabled}>
          {pending ? t('ask.sending') : t('ask.send')}
        </Button>
      </form>

      {providerOff ? (
        <p className="ask-note">
          <Link to={`/explorer?snapshot_id=${pinnedSnapshot}`}>{t('ask.goExplorer')}</Link>
        </p>
      ) : null}

      <CitationDialog
        open={citation != null}
        title={t('ask.citationTitle')}
        onClose={() => {
          sourceRequest.current += 1
          setCitation(null)
          setEvidence(null)
        }}
      >
        {evidenceLoading ? <p role="status">{t('common.loading')}</p> : null}
        {evidenceError ? <p>{evidenceError}</p> : null}
        {evidence ? <div>
          <p>{t('ask.pinned', {id: evidence.snapshot_id})}</p>
          <p>{evidence.evidence.file_path}{evidence.evidence.provenance === 'source' ? ':' + evidence.evidence.start_line + '–' + evidence.evidence.end_line : ''}</p>
        </div> : null}
      </CitationDialog>

      <ConfirmDialog
        open={confirmDelete}
        title={t('ask.deleteTitle')}
        danger
        confirmLabel={t('common.delete')}
        onConfirm={() => void remove()}
        onCancel={() => setConfirmDelete(false)}
      >
        <p>{t('ask.deleteBody')}</p>
      </ConfirmDialog>
    </div>
  )
}

function messageFor(err: unknown, t: TranslateFn, locale: Locale): string {
  if (!(err instanceof RkgApiError)) return formatError(err, locale)
  if (err.code === 'llm_disabled' || err.status === 503) return t('ask.disabled')
  if (err.code === 'llm_timeout' || err.status === 504) return t('ask.timeout')
  if (err.status === 502) return t('ask.providerError')
  if (err.code === 'conversation_busy') return t('ask.busy')
  if (err.code === 'invalid_turn_request') return formatError(err, locale)
  return formatError(err, locale)
}

function CitationDialog({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}) {
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)
  const { t } = useLocale()

  useEffect(() => {
    onCloseRef.current = onClose
  })

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeRef.current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCloseRef.current()
        return
      }
      if (event.key !== 'Tab' || !dialogRef.current) return
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>('button, [href], input, textarea'),
      ).filter((item) => !item.hasAttribute('disabled'))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last?.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      previous?.focus()
    }
  }, [open])

  if (!open) return null
  return (
    <div className="dialog-backdrop" role="presentation" onClick={() => onClose()}>
      <div
        ref={dialogRef}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id={titleId}>{title}</h2>
        <div>{children}</div>
        <div className="dialog-actions">
          <Button ref={closeRef} onClick={onClose}>
            {t('common.close')}
          </Button>
        </div>
      </div>
    </div>
  )
}
