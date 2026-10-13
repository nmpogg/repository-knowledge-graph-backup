import { Button } from '../components/ui/Button'
import { useLocale } from '../i18n'
import type { Citation, ConversationTurn } from '../types/api'
import { previewCoverage, sourceLabel } from './previewClient'

export function PreviewReply({ turn, unavailable, openCitation }: { turn: ConversationTurn; unavailable: boolean; openCitation: (citation: Citation) => void }) {
  const { t, locale } = useLocale()
  const vi = locale === 'vi'
  const coverage = previewCoverage[turn.turn_id]
  return <div className="ask-bubble is-reply">
    <p className="preview-answer">{turn.answer || (turn.status === 'failed' ? t('ask.providerError') : turn.status === 'insufficient_evidence' ? t('ask.insufficient') : null)}</p>
    {turn.citations.length > 0 && <div className="ask-extra"><h2>{vi ? 'Nguồn tham khảo' : 'Sources'}</h2>
      <ul className="ask-cites">{turn.citations.map((item, index) => <li key={`${turn.turn_id}-cite-${index}`}>
        <Button disabled={unavailable} aria-label={`${vi ? 'Mở nguồn' : 'Open source'} ${sourceLabel(item, index + 1, locale)}`} onClick={() => openCitation(item)}>{sourceLabel(item, index + 1, locale)}</Button>
      </li>)}</ul>
    </div>}
    {coverage === 'partial' && <p className="ask-note">{vi ? 'Kết quả hiện có chỉ bao phủ một phần chuỗi gọi vì dữ liệu truy xuất đã chạm giới hạn. Các lượt hội thoại cũ cũng được rút gọn khỏi ngữ cảnh; hãy hỏi hẹp hơn hoặc nhắc lại chi tiết cần dùng.' : 'This answer covers part of the call chain because retrieval reached its limit. Older conversation turns were also left out of context; narrow your question or restate the details you need.'}</p>}
    {coverage === 'legacy' && <p className="ask-note">{vi ? 'Lượt trả lời cũ chưa lưu thông tin giới hạn truy xuất. Chưa xác định được mức độ bao phủ của kết quả này.' : 'This older answer has no saved retrieval limits. Its coverage is unknown.'}</p>}
    {turn.claims.length > 0 && <details className="ask-extra preview-details"><summary>{vi ? 'Chi tiết kiểm chứng' : 'Verification details'}</summary>
      <ul>{turn.claims.map((claim, i) => <li key={claim.edge_id ?? i}>{claim.text}</li>)}</ul>
    </details>}
  </div>
}
