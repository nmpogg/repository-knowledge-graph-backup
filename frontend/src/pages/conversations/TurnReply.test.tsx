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

it.each(['failed', 'interrupted', 'pending'] as const)('hides coverage and old limit notes for %s turns', (status) => {
  render(<TurnReply turn={{...turn, status}} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.queryByText('The answer covers a limited number of entities.')).not.toBeInTheDocument()
  cleanup()
  render(<TurnReply turn={{...turn, status, response_metadata:null}} t={(key, params) => translate('en', key, params)} unavailable={false} legacy={false} onSource={() => {}} />)
  expect(screen.queryByText('Coverage is unknown for this stored turn.')).not.toBeInTheDocument()
})
