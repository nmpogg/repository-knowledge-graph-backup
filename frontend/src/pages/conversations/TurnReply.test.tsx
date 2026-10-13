import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { translate } from '../../i18n/locale'
import type { ConversationTurn } from '../../types/api'
import { TurnReply } from './TurnReply'

afterEach(cleanup)
const turn: ConversationTurn = { turn_id: 'synthetic', sequence: 1, status: 'insufficient_evidence',
  question: 'synthetic', resolved_question: 'synthetic', answer: 'Try an exact method/path.',
  claims: [], citations: [], context_turn_ids: [], error_code: null,
  response_metadata: { version: 1, language: 'en', kind: 'insufficient', subject: null,
    coverage: 'partial', retrieval_truncated: true, history_truncated: false,
    limitations: ['max_nodes'], insufficient_reason: 'entity_not_found' } }

it('shows one insufficient answer and persisted friendly limit after reload', () => {
  render(<TurnReply turn={structuredClone(turn)} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.getAllByText('Try an exact method/path.')).toHaveLength(1)
  expect(screen.queryByText('Not enough evidence in this snapshot.')).not.toBeInTheDocument()
  expect(screen.getByText('The answer covers a limited number of entities.')).toBeInTheDocument()
  expect(screen.queryByText('max_nodes')).not.toBeInTheDocument()
})

it('starts citations closed until the disclosure is opened', () => {
  const cited = { ...turn, citations: [{ snapshot_id: 'snap', entity_id: 'ent', evidence_id: 'ev' }] }
  const { container } = render(<TurnReply turn={cited} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  const details = screen.getByText('Citations').closest('details')
  expect(details).not.toHaveAttribute('open')
  expect(container.querySelector('.ask-cites')).toBeTruthy()
})

it('puts claim text and citation numbers in one closed disclosure', () => {
  const mixed = { ...turn, claims: [{ text: 'a calls b.', edge_id: 'ab', citation_indexes: [0] }],
    citations: [{ snapshot_id: 'snap', entity_id: 'ent', evidence_id: 'ev', edge_id: 'ab' }, { snapshot_id: 'snap', evidence_id: 'ev2' }] }
  render(<TurnReply turn={mixed} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  const details = screen.getByText('Citations').closest('details')
  expect(details).not.toHaveAttribute('open')
  expect(screen.queryByText('Claims')).not.toBeInTheDocument()
  expect(details).toHaveTextContent('a calls b.')
  expect(details).toHaveTextContent('1')
  expect(details).toHaveTextContent('2')
  expect(screen.getByRole('button', { name: 'Open citation 1' })).toHaveTextContent('1')
})

it('starts claims closed and treats legacy coverage as unknown', () => {
  const legacy = { ...turn, response_metadata: null, claims: [{ text: 'a calls b.', edge_id: 'ab' }] }
  const { container } = render(<TurnReply turn={legacy} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(container.querySelector('details')).not.toHaveAttribute('open')
  expect(screen.getByText('Coverage is unknown for this stored turn.')).toBeInTheDocument()
})

it('explains malformed failure naturally and keeps its code in error details', () => {
  const failed = { ...turn, status: 'failed' as const, answer: '', error_code: 'llm_malformed_response', response_metadata: null }
  render(<TurnReply turn={failed} t={(key, params) => translate('vi', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.getByRole('status')).toHaveTextContent('Chatbot chưa tạo được câu trả lời hợp lệ.')
  expect(screen.queryByText('Chưa xác định được phạm vi dữ liệu của lượt đã lưu này.')).not.toBeInTheDocument()
  expect(screen.getByText('llm_malformed_response')).toBeInTheDocument()
  expect(screen.getByText('Thông tin lỗi').closest('details')).not.toHaveAttribute('open')
})

it('shows the decision and keeps the call flow behind a closed disclosure', () => {
  const answered = { ...turn, status: 'answered' as const, answer: 'Bạn có thể đặt phần code mới trong `BookingController.java`.\n\n@@rkg-detail@@\n\nTừ đây, luồng gọi sang `BookingService.cancelBooking`.',
    response_metadata: { ...turn.response_metadata!, kind: 'answer' as const, subject: { entity_id: 'e', type: 'Callable', name: 'BookingController', qualified_name: 'controller.BookingController', method: null, path: null }, coverage: 'complete' as const, retrieval_truncated: false, limitations: [], insufficient_reason: null } }
  render(<TurnReply turn={answered} t={(key, params) => translate('vi', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  const lead = screen.getByText(/BookingController\.java/)
  expect(lead).not.toHaveTextContent('@@rkg-detail@@')
  const more = screen.getByText('Phần mở rộng').closest('details')
  expect(more).not.toHaveAttribute('open')
  expect(more).toHaveTextContent('BookingService.cancelBooking')
})

it.each(['failed', 'interrupted', 'pending'] as const)('hides coverage and old limit notes for %s turns', (status) => {
  render(<TurnReply turn={{...turn, status}} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.queryByText('The answer covers a limited number of entities.')).not.toBeInTheDocument()
  cleanup()
  render(<TurnReply turn={{...turn, status, response_metadata:null}} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.queryByText('Coverage is unknown for this stored turn.')).not.toBeInTheDocument()
})
