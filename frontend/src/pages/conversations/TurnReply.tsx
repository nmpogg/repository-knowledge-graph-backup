import type { Citation, Claim, ConversationTurn } from '../../types/api'
import type { TranslateFn } from '../../i18n'
import { Button } from '../../components/ui/Button'
import { readResponseMetadata } from './responseMetadata'

const ANSWER_DETAIL_MARK = '\n\n@@rkg-detail@@\n\n'

function splitAnswer(answer: string): { lead: string; detail: string } {
  const index = answer.indexOf(ANSWER_DETAIL_MARK)
  if (index < 0) return { lead: answer, detail: '' }
  return { lead: answer.slice(0, index), detail: answer.slice(index + ANSWER_DETAIL_MARK.length) }
}

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
      <AnswerText answer={turn.answer || (turn.status === 'insufficient_evidence' ? t('ask.insufficient') : turn.status === 'pending' ? t('ask.pending') : '')} moreLabel={t('ask.more')} />}
    {malformed ? <details className="ask-extra"><summary>{t('ask.errorDetails')}</summary><code>{turn.error_code}</code></details> : null}
    {completed && (metadata == null || metadata.coverage === 'unknown') ? <p className="ask-note">{t('ask.coverageUnknown')}</p> : null}
    {limits.map((code) => <p className="ask-note" key={code}>{t(('ask.limit.' + code) as Parameters<TranslateFn>[0])}</p>)}
    <Sources turn={turn} t={t} unavailable={unavailable} legacy={legacy} onSource={onSource} />
  </div>
}

function linkedCitationIndexes(claim: Claim, citations: Citation[]): number[] {
  return (claim.citation_indexes ?? []).filter((index) =>
    citations[index]?.edge_id === claim.edge_id && Boolean(citations[index]?.evidence_id))
}

function Sources({ turn, t, unavailable, legacy, onSource }: {
  turn: ConversationTurn; t: TranslateFn; unavailable: boolean; legacy: boolean
  onSource: (turn: ConversationTurn, index: number) => void
}) {
  if (turn.claims.length === 0 && turn.citations.length === 0) return null
  const linked = new Set(turn.claims.flatMap((claim) => linkedCitationIndexes(claim, turn.citations)))
  const loose = turn.citations.map((_, index) => index).filter((index) => !linked.has(index))
  const cite = (index: number) => {
    const label = t('ask.openCitation', { n: index + 1 })
    return turn.citations[index]?.evidence_id
      ? <Button key={index} className="ask-cite-n" disabled={unavailable || legacy} aria-label={label} onClick={() => onSource(turn, index)}>{index + 1}</Button>
      : <span key={index}>{t('ask.sourceMissing', { n: index + 1 })}</span>
  }
  const count = turn.citations.length || turn.claims.length
  return <details className="ask-extra ask-sources">
    <summary><span>{t('ask.citations')}</span><span className="ask-source-count">{count}</span></summary>
    {legacy && turn.citations.length > 0 ? <p>{t('ask.exactSourceUnavailable')}</p> : null}
    {turn.claims.length > 0 ? <ul className="ask-claim-list">{turn.claims.map((claim, index) => {
      const marks = linkedCitationIndexes(claim, turn.citations)
      return <li key={claim.edge_id ?? index}>
        {marks.length > 0 ? <span className="ask-claim-marks">{marks.map(cite)}</span> : null}
        <span className="ask-claim-text">{claim.text}</span>
      </li>
    })}</ul> : null}
    {loose.length > 0 ? <div className="ask-cites">{loose.map(cite)}</div> : null}
  </details>
}

function AnswerText({ answer, moreLabel }: { answer: string; moreLabel: string }) {
  const { lead, detail } = splitAnswer(answer)
  return <>
    <p className="ask-answer">{lead}</p>
    {detail ? <details className="ask-extra ask-more"><summary>{moreLabel}</summary><p className="ask-answer">{detail}</p></details> : null}
  </>
}
