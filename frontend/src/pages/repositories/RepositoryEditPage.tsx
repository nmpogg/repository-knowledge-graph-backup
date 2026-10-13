import { AlertTriangle, ArrowLeft } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { useLocale } from '../../i18n'
import { formatError } from '../../lib/format'
import { RkgApiError, type Repository } from '../../types/api'

export function RepositoryEditPage() {
  const { repositoryId = '' } = useParams()
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const summaryRef = useRef<HTMLDivElement>(null)
  const nameRef = useRef<HTMLInputElement>(null)
  const errorSummaryId = useId()

  const [repo, setRepo] = useState<Repository | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [displayName, setDisplayName] = useState('')
  const [sourceRoot, setSourceRoot] = useState('.')
  const [appModule, setAppModule] = useState('')
  const [appSymbol, setAppSymbol] = useState('')
  const [expectedRevision, setExpectedRevision] = useState(0)

  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [conflict, setConflict] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setLoadError(null)
      try {
        const r = await client.getRepository(repositoryId)
        if (cancelled) return
        setRepo(r)
        setDisplayName(r.display_name)
        setSourceRoot(r.source_root ?? '.')
        setAppModule(r.app_module ?? '')
        setAppSymbol(r.app_symbol ?? '')
        setExpectedRevision(r.revision)
      } catch (err) {
        if (!cancelled) setLoadError(formatError(err, locale))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [client, repositoryId, locale])

  const reloadServerState = async () => {
    const r = await client.getRepository(repositoryId)
    setRepo(r)
    setExpectedRevision(r.revision)
    announce(t('repo.edit.reloaded'))
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setConflict(false)
    setFieldErrors({})
    setSubmitting(true)
    try {
      const updated = await client.updateRepository(repositoryId, {
        expected_revision: expectedRevision,
        display_name: displayName,
        source_root: sourceRoot || '.',
        app_module: appModule || null,
        app_symbol: appSymbol || null,
      })
      announce(t('repo.edit.saved', { name: updated.display_name }))
      navigate(`/repositories/${updated.repository_id}`)
    } catch (err) {
      const message = formatError(err, locale)
      setFormError(message)
      announce(message, true)
      if (err instanceof RkgApiError && err.code === 'repository_conflict') {
        setConflict(true)
        queueMicrotask(() => summaryRef.current?.focus())
      } else if (err instanceof RkgApiError && err.code === 'invalid_input') {
        const lower = message.toLowerCase()
        if (lower.includes('tên hiển thị') || lower.includes('display name')) {
          setFieldErrors({ display_name: message })
          queueMicrotask(() => nameRef.current?.focus())
        } else {
          queueMicrotask(() => summaryRef.current?.focus())
        }
      } else {
        queueMicrotask(() => summaryRef.current?.focus())
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="page repo-mgmt">
        <div className="state-block" aria-busy="true">
          <h2>{t('repo.edit.loading')}</h2>
        </div>
      </div>
    )
  }

  if (loadError || !repo) {
    return (
      <div className="page repo-mgmt">
        <div className="state-block error" role="alert">
          <h2>{t('repo.edit.unavailable')}</h2>
          <p>{loadError ?? t('common.notFound')}</p>
          <Button onClick={() => navigate('/repositories')}>{t('repo.edit.backList')}</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="page repo-mgmt">
      <header className="page-header">
        <div>
          <p className="repo-eyebrow">
            <Link to={`/repositories/${repo.repository_id}`}>
              <ArrowLeft size={14} aria-hidden />
              {repo.display_name}
            </Link>
          </p>
          <h1>{t('repo.edit.title')}</h1>
          <p>{t('repo.edit.lead')}</p>
        </div>
        <Button onClick={() => navigate(`/repositories/${repo.repository_id}`)}>
          {t('common.cancel')}
        </Button>
      </header>

      <form className="form-stack panel panel-pad repo-form" onSubmit={onSubmit} noValidate>
        {formError ? (
          <div
            ref={summaryRef}
            id={errorSummaryId}
            className={`state-block error repo-alert${conflict ? ' is-conflict' : ''}`}
            role="alert"
            tabIndex={-1}
            style={{ padding: 12 }}
          >
            <div className="row-actions" style={{ alignItems: 'flex-start' }}>
              <AlertTriangle size={18} aria-hidden />
              <div>
                <strong>
                  {conflict ? t('repo.edit.conflictTitle') : t('repo.edit.saveFailed')}
                </strong>
                <p>{formError}</p>
                {conflict ? (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => void reloadServerState()}
                  >
                    {t('repo.edit.reloadRev')}
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        <div className="field">
          <label>{t('repo.edit.sourceReadonly')}</label>
          <div className="repo-readonly">
            <Badge>{repo.source_type}</Badge>
            <code className="mono">{repo.source_locator_redacted}</code>
            <span className="muted">rev {expectedRevision}</span>
          </div>
          <span className="hint">
            {t('repo.edit.sourceHint')}
          </span>
        </div>

        <div className="field">
          <label htmlFor="edit_display_name">{t('repo.edit.displayName')}</label>
          <input
            ref={nameRef}
            id="edit_display_name"
            name="display_name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            autoComplete="off"
            aria-invalid={Boolean(fieldErrors.display_name)}
            aria-describedby={formError ? errorSummaryId : undefined}
          />
          {fieldErrors.display_name ? (
            <span className="error">{fieldErrors.display_name}</span>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="edit_source_root">{t('repo.edit.sourceRoot')}</label>
          <input
            id="edit_source_root"
            value={sourceRoot}
            onChange={(e) => setSourceRoot(e.target.value)}
          />
          <span className="hint">
            {t('repo.edit.sourceRootHint')} <code>.</code>
          </span>
        </div>

        <div className="field">
          <label htmlFor="edit_app_module">{t('repo.edit.appModule')}</label>
          <input
            id="edit_app_module"
            value={appModule}
            onChange={(e) => setAppModule(e.target.value)}
            placeholder="app.main"
          />
        </div>

        <div className="field">
          <label htmlFor="edit_app_symbol">{t('repo.edit.appSymbol')}</label>
          <input
            id="edit_app_symbol"
            value={appSymbol}
            onChange={(e) => setAppSymbol(e.target.value)}
            placeholder="app"
          />
        </div>

        <div className="row-actions">
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? t('repo.edit.saving') : t('repo.edit.save')}
          </Button>
          <Link to={`/repositories/${repo.repository_id}`} className="btn btn-ghost">
            {t('repo.edit.backDetail')}
          </Link>
        </div>
      </form>
    </div>
  )
}
