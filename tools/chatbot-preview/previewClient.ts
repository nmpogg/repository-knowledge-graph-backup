// Synthetic UX data only. No model, graph retrieval, persistence, or public API proposal.
import { createMockClient, type RkgClient } from '../client/mock/mockClient'
import { DEMO_REPO_ID, DEMO_SNAPSHOT_ID, seedEntities } from '../client/mock/fixtures'
import { RkgApiError } from '../types/api'
import type { Citation, ConversationHistory, ConversationTurn, EntityDetail, TurnSubmitResult } from '../types/api'

export const previewCases = [
  ['answer', 'Trả lời trực tiếp / gián tiếp'],
  ['answer-en', 'Natural answer in English'],
  ['clarify', 'Tên trùng · chọn đúng entity'],
  ['missing', 'Không tìm thấy entity'],
  ['relation', 'Thiếu quan hệ trong snapshot'],
  ['partial', 'Kết quả một phần + lịch sử rút gọn'],
  ['legacy', 'Lượt cũ · chưa rõ độ bao phủ'],
  ['greeting', 'Chào bằng tiếng Việt không dấu'],
  ['english', 'Greeting in English'],
  ['empty', 'Hội thoại mới'],
  ['disabled', 'LLM chưa cấu hình · thử Gửi'],
  ['timeout', 'Quá thời gian · thử Gửi'],
  ['conflict', 'Xung đột revision · thử Gửi'],
  ['unavailable', 'Snapshot không khả dụng'],
  ['safe', 'Văn bản chứa thẻ HTML'],
  ['long', 'Tên qualified dài · kiểm tra wrap'],
] as const

const subject = seedEntities.find((e) => e.id === 'ent-endpoint-get-order')!
const handler = seedEntities.find((e) => e.id === 'ent-fn-get-order')!
const service = seedEntities.find((e) => e.id === 'ent-fn-load-order')!
const answer = 'Endpoint GET /orders/{id} được xử lý bởi get_order. Hàm xử lý này gọi trực tiếp load_order để lấy đơn hàng.\n\nỞ bước tiếp theo, load_order gọi OrderRepository.load. Vì vậy, OrderRepository.load nằm trong chuỗi gọi gián tiếp từ hàm xử lý endpoint.'
const sources: Record<string, { entity: string; path: string; line: number }> = {
  'preview-ev-direct': { entity: handler.id, path: 'app/api/orders.py', line: 42 },
  'preview-ev-indirect': { entity: service.id, path: 'app/services/orders.py', line: 18 },
}
export function sourceLabel(citation: Citation, ordinal: number, locale: string) {
  const source = sources[citation.evidence_id ?? '']
  return source ? `${source.path}:${source.line}` : `${locale === 'vi' ? 'Nguồn' : 'Source'} ${ordinal}`
}
export function exactEvidence(detail: EntityDetail, citation: Citation): EntityDetail {
  const source = sources[citation.evidence_id ?? '']
  if (!source || citation.snapshot_id !== DEMO_SNAPSHOT_ID || source.entity !== detail.id) {
    return { ...detail, evidence: [] }
  }
  return { ...detail, evidence: [{ provenance: 'source', relative_path: source.path, start_line: source.line }] }
}
export const previewCoverage: Record<string, 'partial' | 'legacy' | 'complete'> = {}
export function focusLabel(id: string) {
  return seedEntities.find((e) => e.id === id)?.name ?? id
}
export function candidateLabel(id: string, ordinal: number, locale: string) {
  const entity = seedEntities.find((e) => e.id === id)
  const kind = id === subject.id ? 'Endpoint' : id === handler.id ? (locale === 'vi' ? 'Hàm xử lý' : 'Handler') : (locale === 'vi' ? 'Hàm dịch vụ' : 'Service function')
  return `${ordinal}. ${kind} · ${id === subject.id ? entity?.name : entity?.qualified_name}`
}

export function createPreviewClient(): RkgClient {
  const base = createMockClient()
  const histories = new Map<string, ConversationHistory>()
  let newCount = 0
  const seed = (id: string) => {
    const scenario = id.replace('preview-', '')
    const turn: ConversationTurn = {
      turn_id: `${id}-turn-1`, sequence: 1, status: 'answered',
      question: 'endpoint get_order dang goi nhung func nao', resolved_question: null,
      answer, claims: [
        { text: 'app.api.orders:get_order calls app.services.orders:load_order.', edge_id: 'preview-edge-direct' },
        { text: 'app.services.orders:load_order calls app.repositories.orders:OrderRepository.load.', edge_id: 'preview-edge-indirect' },
      ], citations: Object.entries(sources).map(([evidence_id, s]) => ({ snapshot_id: DEMO_SNAPSHOT_ID, entity_id: s.entity, evidence_id })),
      context_turn_ids: [], error_code: null,
    }
    if (scenario === 'clarify') {
      turn.status = 'needs_clarification'
      turn.answer = 'Tên get_order có thể chỉ endpoint hoặc hàm xử lý. Bạn muốn xem lời gọi từ mục nào? Chọn một mục bên dưới để tôi tiếp tục câu hỏi về các hàm được gọi.'
    }
    if (scenario === 'missing' || scenario === 'relation') {
      turn.status = 'insufficient_evidence'
      turn.answer = scenario === 'missing'
        ? 'Tôi chưa tìm thấy endpoint login trong snapshot này. Bạn có thể thử tên hàm xử lý hoặc METHOD và đường dẫn, ví dụ POST /login.'
        : 'Tôi tìm thấy endpoint GET /orders/{id}, nhưng snapshot chưa có bằng chứng về các hàm được gọi từ hàm xử lý. Bạn có thể kiểm tra endpoint trong Explorer hoặc lập chỉ mục lại repository.'
      if (scenario === 'missing') turn.question = 'endpoint login gọi những hàm nào?'
    }
    if (scenario === 'greeting' || scenario === 'english') {
      turn.question = scenario === 'greeting' ? 'alo' : 'hello'
      turn.answer = scenario === 'greeting'
        ? 'Chào bạn! Bạn có thể hỏi endpoint gọi hàm nào, hàm đọc hoặc ghi bảng nào, hay sự kiện được phát ở đâu. Ví dụ: “GET /orders/{id} gọi những hàm nào?”'
        : 'Hello! You can ask which functions an endpoint calls, which tables a function reads or writes, or where an event is emitted. Try: “Which functions does GET /orders/{id} call?”'
    }
    if (scenario === 'safe') turn.answer = '<script>alert(1)</script> là văn bản mẫu để kiểm tra hiển thị an toàn.'
    if (scenario === 'answer-en') {
      turn.question = 'Which functions does GET /orders/{id} call?'
      turn.answer = 'GET /orders/{id} is handled by get_order. This handler directly calls load_order to fetch an order.\n\nNext, load_order calls OrderRepository.load. OrderRepository.load is therefore part of the indirect call chain from the endpoint handler.'
    }
    if (scenario === 'long') turn.answer = 'Tên đầy đủ của hàm trong dữ liệu mẫu này là app.services.orders.order_management_for_international_customers_and_partner_integrations.OrderService.load_order_with_all_related_order_items_and_customer_shipping_preferences.\n\nHãy kiểm tra tên dài vẫn đọc được trên màn hình hẹp.'
    if (!['answer', 'answer-en', 'partial', 'legacy', 'unavailable'].includes(scenario)) { turn.claims = []; turn.citations = [] }
    previewCoverage[turn.turn_id] = scenario === 'partial' ? 'partial' : scenario === 'legacy' ? 'legacy' : 'complete'
    const history: ConversationHistory = {
      conversation: {
        conversation_id: id, repository_id: DEMO_REPO_ID, snapshot_id: DEMO_SNAPSHOT_ID,
        title: `Ask · ${previewCases.find(([key]) => key === scenario)?.[1] ?? 'Hội thoại mới'}`,
        revision: 2, focus_entity_id: ['empty', 'greeting', 'english', 'missing'].includes(scenario) ? null : subject.id,
        created_at: '2026-10-06T03:00:00Z', updated_at: '2026-10-06T03:00:00Z',
      },
      turns: { items: ['empty', 'disabled', 'timeout', 'conflict'].includes(scenario) || scenario.startsWith('new-') ? [] : [turn], page: { offset: 0, limit: 100, total: 1 } },
      candidate_entities: scenario === 'clarify' ? [subject, handler, service] : [],
    }
    history.turns.page.total = history.turns.items.length
    histories.set(id, history)
    return history
  }
  const get = (id: string) => histories.get(id) ?? seed(id)
  return {
    ...base,
    async getConversation(id) { return structuredClone(get(id)) },
    async getSnapshot(repo, snapshot) { return base.getSnapshot(repo, snapshot) },
    async listConversations() {
      const items = previewCases.map(([scenario]) => structuredClone(get(`preview-${scenario}`).conversation))
      return { items, page: { offset: 0, limit: 100, total: items.length } }
    },
    async createConversation() { return structuredClone(seed(`preview-new-${++newCount}`).conversation) },
    async deleteConversation(id) { histories.delete(id) },
    async submitTurn(id, body): Promise<TurnSubmitResult> {
      await new Promise((resolve) => setTimeout(resolve, 650))
      const history = get(id)
      if (id === 'preview-disabled') throw new RkgApiError(503, 'llm_disabled', 'Synthetic provider disabled')
      if (id === 'preview-timeout') throw new RkgApiError(504, 'llm_timeout', 'Synthetic timeout')
      if (id === 'preview-unavailable') throw new RkgApiError(410, 'snapshot_unavailable', 'Synthetic unavailable')
      if (id === 'preview-conflict' || body.expected_revision !== history.conversation.revision) throw new RkgApiError(409, 'conversation_conflict', 'Synthetic revision conflict')
      const original = history.turns.items.at(-1)
      const chosen = body.root_id ?? (/^[1-3]$/.test(body.question.trim()) ? history.candidate_entities[Number(body.question) - 1]?.id : undefined)
      const turn: ConversationTurn = {
        turn_id: `${id}-turn-${history.turns.items.length + 1}`, sequence: history.turns.items.length + 1,
        question: body.question, resolved_question: chosen ? original?.question ?? null : null,
        status: 'answered', answer: chosen ? `Bạn đã chọn ${focusLabel(chosen)}.\n\n${chosen === service.id ? 'Hàm dịch vụ load_order gọi trực tiếp OrderRepository.load.' : answer}` : 'Đây là dữ liệu mẫu của preview. Chọn tình huống ở phía trên để xem cách trình bày từng loại phản hồi.',
        claims: [], citations: [], context_turn_ids: [], error_code: null,
      }
      previewCoverage[turn.turn_id] = 'complete'
      history.turns.items.push(turn)
      history.turns.page.total = history.turns.items.length
      history.candidate_entities = []
      if (chosen) history.conversation.focus_entity_id = chosen
      history.conversation.revision += 1
      return { ...structuredClone(turn), schema_version: '1', conversation_id: id,
        revision: history.conversation.revision, repository_id: DEMO_REPO_ID, snapshot_id: DEMO_SNAPSHOT_ID,
        candidate_entities: [], limitations: [], retrieval_truncated: false, history_truncated: false, usage: null }
    },
  }
}
