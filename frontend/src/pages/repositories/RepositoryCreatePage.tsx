import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Button } from '../../components/ui/Button'
import { useLocale } from '../../i18n'
import { formatError } from '../../lib/format'
import { RkgApiError } from '../../types/api'

export function RepositoryCreatePage() {
  const client = getRkgClient()
  const navigate = useNavigate()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()

  const [displayName, setDisplayName] = useState('')
  const [path, setPath] = useState('')
  const [sourceRoot, setSourceRoot] = useState('.')
  const [appModule, setAppModule] = useState('')
  const [appSymbol, setAppSymbol] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFieldErrors({})
    setSubmitting(true)
    try {
      const repo = await client.createRepository({
        display_name: displayName,
        source_type: 'local',
        path,
        source_root: sourceRoot || undefined,
        app_module: appModule || undefined,
        app_symbol: appSymbol || undefined,
      })
      announce(t('repo.create.created', { name: repo.display_name }))
      navigate(`/repositories/${repo.repository_id}`)
    } catch (err) {
      const message = formatError(err, locale)
      setFormError(message)
      announce(message, true)
      if (
        err instanceof RkgApiError &&
        (err.code === 'invalid_input' ||
          err.code === 'invalid_request' ||
          err.code.startsWith('source_'))
      ) {
        const lower = message.toLowerCase()
        if (lower.includes('đường dẫn') || lower.includes('path')) {
          setFieldErrors({ path: message })
        } else if (lower.includes('tên hiển thị') || lower.includes('display name')) {
          setFieldErrors({ display_name: message })
        }
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page repo-mgmt">
      <header className="page-header">
        <div>
          <h1>{t('repo.create.title')}</h1>
          <p>{t('repo.create.lead')}</p>
        </div>
        <Button onClick={() => navigate('/repositories')}>{t('common.cancel')}</Button>
      </header>

      <form className="form-stack panel panel-pad repo-form" onSubmit={onSubmit} noValidate>
        {formError ? (
          <div className="state-block error" role="alert" style={{ padding: 12 }}>
            <p>{formError}</p>
          </div>
        ) : null}

        <div className="field">
          <label htmlFor="display_name">{t('repo.create.displayName')}</label>
          <input
            id="display_name"
            name="display_name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            autoComplete="off"
            aria-invalid={Boolean(fieldErrors.display_name)}
          />
          {fieldErrors.display_name ? (
            <span className="error">{fieldErrors.display_name}</span>
          ) : (
            <span className="hint">{t('repo.create.displayHint')}</span>
          )}
        </div>

        <div className="field">
          <label htmlFor="path">{t('repo.create.path')}</label>
          <input
            id="path"
            name="path"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            required
            autoComplete="off"
            placeholder={t('repo.create.pathPlaceholder')}
            aria-invalid={Boolean(fieldErrors.path)}
          />
          {fieldErrors.path ? (
            <span className="error">{fieldErrors.path}</span>
          ) : (
            <span className="hint">{t('repo.create.pathHint')}</span>
          )}
        </div>

        <details>
          <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
            {t('repo.create.advanced')}
          </summary>
          <div className="stack-4" style={{ marginTop: 12 }}>
            <div className="field">
              <label htmlFor="source_root">{t('repo.create.sourceRoot')}</label>
              <input
                id="source_root"
                value={sourceRoot}
                onChange={(e) => setSourceRoot(e.target.value)}
              />
              <span className="hint">
                {t('repo.create.sourceRootHint')} <code>.</code>
              </span>
            </div>
            <div className="field">
              <label htmlFor="app_module">{t('repo.create.appModule')}</label>
              <input
                id="app_module"
                value={appModule}
                onChange={(e) => setAppModule(e.target.value)}
                placeholder="app.main"
              />
            </div>
            <div className="field">
              <label htmlFor="app_symbol">{t('repo.create.appSymbol')}</label>
              <input
                id="app_symbol"
                value={appSymbol}
                onChange={(e) => setAppSymbol(e.target.value)}
                placeholder="app"
              />
            </div>
          </div>
        </details>

        <div className="row-actions">
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? t('repo.create.submitting') : t('repo.create.submit')}
          </Button>
          <Link to="/repositories" className="btn btn-ghost">
            {t('repo.create.backList')}
          </Link>
        </div>
      </form>
    </div>
  )
}
