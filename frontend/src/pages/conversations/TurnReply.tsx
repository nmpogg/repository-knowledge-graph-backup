import type { ConversationTurn } from '../../types/api'
import type { TranslateFn } from '../../i18n'
import { Button } from '../../components/ui/Button'
import { readResponseMetadata } from './responseMetadata'

export function TurnReply({ turn, t, unavailable, legacy, onSource }: {
  turn: ConversationTurn; t: TranslateFn; unavailable: boolean; legacy: boolean
  onSource: (turn: ConversationTurn, index: number) => void
}) {
  const metadata = readResponseMetadata(turn.response_metadata)
  const error = turn.status === 'failed' || turn.status === 'interrupted'
  const completed = ['answered', 'insufficient_evidence', 'needs_clarification'].includes(turn.status)
  const malformed = error && turn.error_code === 'llm_malformed_response'
  const limits = completed ? metadata?.limitations ?? [] : []
  return <div className="ask-bubble is-reply">
    {error ? <p role="status">{malformed ? t('ask.malformedTurn') : t('ask.failedTurn', { code: turn.error_code ?? turn.status })}</p> :
      <p className="ask-answer">{turn.answer || (turn.status === 'insufficient_evidence' ? t('ask.insufficient') : turn.status === 'pending' ? t('ask.pending') : '')}</p>}
    {malformed ? <details className="ask-extra"><summary>{t('ask.errorDetails')}</summary><code>{turn.error_code}</code></details> : null}
    {completed && (metadata == null || metadata.coverage === 'unknown') ? <p className="ask-note">{t('ask.coverageUnknown')}</p> : null}
    {limits.map((code) => <p className="ask-note" key={code}>{t(('ask.limit.' + code) as Parameters<TranslateFn>[0])}</p>)}
    {turn.claims.length > 0 ? <details className="ask-extra"><summary>{t('ask.claims')}</summary>
      <ul>{turn.claims.map((claim, index) => <li key={claim.edge_id ?? index}>{claim.text}
        {claim.citation_indexes?.filter((i) => turn.citations[i]?.edge_id === claim.edge_id && Boolean(turn.citations[i]?.evidence_id)).map((i) =>
          <Button key={i} disabled={unavailable || legacy} onClick={() => onSource(turn, i)}>{t('ask.openCitation', {n: i + 1})}</Button>)}
      </li>)}</ul>
    </details> : null}
    {turn.citations.length > 0 ? <div className="ask-extra"><h2>{t('ask.citations')}</h2>
      {legacy ? <p>{t('ask.exactSourceUnavailable')}</p> : null}
      <ul className="ask-cites">{turn.citations.map((citation, index) => <li key={index}>
        {citation.evidence_id ? <Button disabled={unavailable || legacy} aria-label={t('ask.openCitation', { n: index + 1 })} onClick={() => onSource(turn, index)}>
          {t('ask.openCitation', { n: index + 1 })}
        </Button> : <span>{t('ask.sourceMissing', { n: index + 1 })}</span>}
      </li>)}</ul>
    </div> : null}
  </div>
}
