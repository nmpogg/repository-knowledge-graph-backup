import { CheckCircle2, Network, RefreshCw } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRkgClient } from '../../client'
import { useAnnouncer } from '../../components/ui/Announcer'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { useJobPolling } from '../../hooks/useJobPolling'
import { useLocale } from '../../i18n'
import { formatError, shortId } from '../../lib/format'
import type { JobStage } from '../../types/api'

function stageIndex(stage: JobStage): number {
  if (stage === 'queued') return 0
  if (stage === 'detecting') return 1
  if (stage === 'indexing') return 2
  return 3
}

export function JobMonitorPage() {
  const { jobId = '' } = useParams()
  const navigate = useNavigate()
  const client = getRkgClient()
  const { announce } = useAnnouncer()
  const { t, locale } = useLocale()
  const { job, error, loading } = useJobPolling(jobId)
  const [selectedApp, setSelectedApp] = useState<string>('')
  const [submittingApp, setSubmittingApp] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const candidates = job?.report?.app_candidates ?? []
  const needsAppSelection =
    job?.stage === 'detecting' &&
    candidates.length > 1 &&
    !job.report?.selected_app_id

  const activeIdx = job ? stageIndex(job.stage) : 0

  const stages = [
    { id: 'queued' as const, label: t('job.stage.queued') },
    { id: 'detecting' as const, label: t('job.stage.detecting') },
    { id: 'indexing' as const, label: t('job.stage.indexing') },
    { id: 'terminal' as const, label: t('job.stage.terminal') },
  ]

  const tone = useMemo(() => {
    if (!job) return 'neutral' as const
    if (job.stage === 'failed') return 'error' as const
    if (job.stage === 'succeeded_with_warnings') return 'warning' as const
    if (job.stage === 'succeeded') return 'success' as const
    return 'info' as const
  }, [job])

  const submitApp = async () => {
    if (!job || !selectedApp) return
    setSubmittingApp(true)
    setLocalError(null)
    try {
      const next = await client.startIndexJob(job.repository_id, {
        app_candidate_id: selectedApp,
      })
      announce(t('job.continued', { id: selectedApp }))
      navigate(`/jobs/${next.job_id}`, { replace: true })
    } catch (err) {
      setLocalError(formatError(err, locale))
      announce(formatError(err, locale), true)
    } finally {
      setSubmittingApp(false)
    }
  }

  if (loading && !job) {
    return (
      <div className="page">
        <div className="state-block" aria-busy="true">
          <h2>{t('job.loading')}</h2>
        </div>
      </div>
    )
  }

  if ((error && !job) || !job) {
    return (
      <div className="page">
        <div className="state-block error" role="alert">
          <h2>{t('job.unavailable')}</h2>
          <p>{error ?? t('common.notFound')}</p>
          <Button onClick={() => navigate('/repositories')}>{t('common.back')}</Button>
        </div>
      </div>
    )
  }

  const terminal = ['succeeded', 'succeeded_with_warnings', 'failed'].includes(job.stage)

  return (
    <div className="page stack-6">
      <header className="page-header">
        <div>
          <h1>{t('job.title')}</h1>
          <p>
            <code className="mono">{job.job_id}</code>
            {' · '}
            {t('job.repoLink')}{' '}
            <Link to={`/repositories/${job.repository_id}`}>
              {shortId(job.repository_id, 14)}
            </Link>
          </p>
        </div>
        <Badge tone={tone}>{job.stage.replaceAll('_', ' ')}</Badge>
      </header>

      <div className="stepper" aria-label={t('job.stages')}>
        {stages.map((s, i) => (
          <div
            key={s.id}
            className="step"
            data-active={i === activeIdx}
            data-done={i < activeIdx}
          >
            {i < activeIdx ? <CheckCircle2 size={14} aria-hidden /> : null}
            {s.label}
          </div>
        ))}
      </div>

      <section className="panel panel-pad stack-3">
        <h2 className="section-title">{t('job.status')}</h2>
        <p>{job.message}</p>
        <p className="muted">
          {t('job.updated', { when: job.updated_at, rev: job.progress_revision })}
        </p>
        {error ? (
          <div className="chip-row">
            <Badge tone="warning">{t('job.pollError')}</Badge>
            <span className="muted">{error}</span>
          </div>
        ) : null}
      </section>

      {needsAppSelection ? (
        <section className="panel panel-pad stack-4" aria-labelledby="app-select-title">
          <h2 id="app-select-title" className="section-title">
            {t('job.selectAppTitle')}
          </h2>
          <p className="muted">{t('job.selectAppLead')}</p>
          <fieldset className="stack-3" style={{ border: 'none', padding: 0, margin: 0 }}>
            <legend className="sr-only">{t('job.candidatesLegend')}</legend>
            {candidates.map((c) => (
              <label
                key={c.candidate_id}
                style={{
                  display: 'flex',
                  gap: 12,
                  alignItems: 'flex-start',
                  padding: 12,
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  cursor: 'pointer',
                }}
              >
                <input
                  type="radio"
                  name="app_candidate"
                  value={c.candidate_id}
                  checked={selectedApp === c.candidate_id}
                  onChange={() => setSelectedApp(c.candidate_id)}
                />
                <span>
                  <strong className="mono">
                    {c.module}:{c.symbol}
                  </strong>
                  <br />
                  <span className="muted">
                    {c.candidate_id} · evidence {c.evidence}
                  </span>
                </span>
              </label>
            ))}
          </fieldset>
          {job.report?.technologies?.length ? (
            <div>
              <h3 style={{ fontSize: 14, margin: '0 0 8px' }}>{t('job.techDetected')}</h3>
              <div className="chip-row">
                {job.report.technologies.map((tech) => (
                  <Badge key={tech.technology}>
                    {tech.technology} · {tech.support_state.replaceAll('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
          {localError ? (
            <p className="error" role="alert">
              {localError}
            </p>
          ) : null}
          <Button
            variant="primary"
            disabled={!selectedApp || submittingApp}
            onClick={() => void submitApp()}
          >
            {submittingApp ? t('job.submitting') : t('job.continue')}
          </Button>
        </section>
      ) : null}

      {job.stage === 'succeeded_with_warnings' && job.snapshot_id ? (
        <div className="state-block">
          <h2>{t('job.warnTitle')}</h2>
          <p>{t('job.warnBody')}</p>
          <Button
            variant="primary"
            onClick={() =>
              navigate(`/explorer?snapshot_id=${encodeURIComponent(job.snapshot_id!)}`)
            }
          >
            <Network size={16} aria-hidden />
            {t('job.openExplorer')}
          </Button>
        </div>
      ) : null}

      {job.report && !needsAppSelection ? (
        <section className="panel panel-pad stack-3">
          <h2 className="section-title">{t('job.report')}</h2>
          <p>{job.report.summary}</p>
          {job.report.warnings.length > 0 ? (
            <ul>
              {job.report.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">{t('job.noWarnings')}</p>
          )}
        </section>
      ) : null}

      {job.stage === 'failed' ? (
        <div className="state-block error" role="alert">
          <h2>{t('job.failedTitle')}</h2>
          <p>
            {t('job.failedBody', {
              message: job.error?.message ?? t('job.failedFallback'),
            })}
          </p>
          <div className="row-actions">
            <Button
              variant="primary"
              onClick={() => navigate(`/repositories/${job.repository_id}`)}
            >
              {t('job.viewRepo')}
            </Button>
          </div>
        </div>
      ) : null}

      {job.stage === 'succeeded' && job.snapshot_id ? (
        <div className="state-block">
          <h2>{t('job.successTitle')}</h2>
          <p>{t('job.successBody', { id: shortId(job.snapshot_id, 16) })}</p>
          <Button
            variant="primary"
            onClick={() =>
              navigate(`/explorer?snapshot_id=${encodeURIComponent(job.snapshot_id!)}`)
            }
          >
            <Network size={16} aria-hidden />
            {t('job.openExplorer')}
          </Button>
        </div>
      ) : null}

      {!terminal ? (
        <p className="muted" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RefreshCw size={14} aria-hidden />
          {t('job.polling')}
        </p>
      ) : null}
    </div>
  )
}
