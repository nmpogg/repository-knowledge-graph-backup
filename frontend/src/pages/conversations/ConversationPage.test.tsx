import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AnnouncerProvider } from '../../components/ui/Announcer'
import { LocaleProvider } from '../../i18n'
import { getRkgClient } from '../../client'
import { ConversationPage } from './ConversationPage'
import { ConversationsPage } from './ConversationsPage'
import { RkgApiError } from '../../types/api'

afterEach(() => {
  vi.restoreAllMocks()
  cleanup()
  localStorage.removeItem('rkg-locale')
})

function renderAsk(path = '/conversations') {
  return render(
    <LocaleProvider>
      <AnnouncerProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/conversations" element={<ConversationsPage />} />
            <Route path="/conversations/:conversationId" element={<ConversationPage />} />
            <Route path="/explorer" element={<h1>Explorer</h1>} />
            <Route path="/repositories/:repositoryId" element={<h1>Repository</h1>} />
          </Routes>
        </MemoryRouter>
      </AnnouncerProvider>
    </LocaleProvider>,
  )
}

describe('conversation UI', () => {
  it('keeps repository text as text and restores focus after closing citation', async () => {
    renderAsk('/conversations/conv-orders-demo')
    expect(await screen.findByRole('heading', { name: 'Order flow' })).toBeInTheDocument()
    const answer = screen.getByText(/<script>alert\(1\)<\/script>/)
    expect(answer.querySelector('script')).toBeNull()
    expect(answer.innerHTML).toContain('&lt;script&gt;')
    const citation = screen.getByRole('button', { name: 'Open citation 1' })
    citation.focus()
    fireEvent.click(citation)
    expect(await screen.findByRole('dialog', { name: 'Citation evidence' })).toBeInTheDocument()
    expect(await screen.findByText(/app\/models\.py:\d+/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    await waitFor(() => expect(citation).toHaveFocus())
  })

  it('selects a clarification candidate explicitly and keeps a conflicting draft', async () => {
    renderAsk('/conversations/conv-orders-demo')
    expect(await screen.findByRole('heading', { name: 'Order flow' })).toBeInTheDocument()
    const newer = await screen.findByRole('button', { name: 'New conversation' })
    await waitFor(() => expect(newer).toBeEnabled())
    fireEvent.click(newer)
    await waitFor(() =>
      expect(screen.queryByRole('heading', { name: 'Order flow' })).not.toBeInTheDocument(),
    )
    const box = await screen.findByLabelText('Question')
    await waitFor(() => expect(box).toBeEnabled())
    fireEvent.change(box, { target: { value: 'Which API owns this?' } })
    fireEvent.submit(box.closest('form')!)
    const choice = await screen.findByRole('button', {
      name: /Candidate 1: endpoint app\.api\.orders:get_order/,
    })
    await waitFor(() => expect(choice).toBeEnabled())
    fireEvent.click(choice)
    expect(await screen.findByText(/app\.api\.orders:get_order reads the orders table/)).toBeInTheDocument()

    const client = getRkgClient()
    const listed = await client.listConversations({ limit: 100 })
    const created = listed.items.find((item) => item.title === '')
    expect(created).toBeTruthy()
    const history = await client.getConversation(created!.conversation_id)
    await client.submitTurn(created!.conversation_id, {
      question: 'another tab',
      client_request_id: 'other-tab',
      expected_revision: history.conversation.revision,
    })
    fireEvent.change(box, { target: { value: 'still my draft' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    expect(await screen.findByRole('button', { name: 'Reload conversation' })).toBeInTheDocument()
    expect(box).toHaveValue('still my draft')
    expect(created?.conversation_id).toBeTruthy()
  })

  it('keeps the draft when the provider is disabled and offers Explorer', async () => {
    renderAsk('/conversations/conv-orders-demo')
    expect(await screen.findByText(/Pinned snapshot snap-orders/)).toBeInTheDocument()
    const box = screen.getByLabelText('Question')
    fireEvent.change(box, { target: { value: 'provider disabled for this snapshot' } })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/not configured/)
    expect(box).toHaveValue('provider disabled for this snapshot')
    expect(screen.getByRole('link', { name: 'Go to Explorer' })).toBeInTheDocument()
  })
})

it('disables submit when capabilities say provider disabled', async () => {
  const client = getRkgClient()
  vi.spyOn(client, 'getConversationCapabilities').mockResolvedValue({schema_version:'rkg.conversation-capabilities/1',features:['ui_locale','response_metadata_v1','exact_citation_lookup','history_unavailable'],provider_enabled:false})
  renderAsk('/conversations/conv-orders-demo')
  expect(await screen.findByText(/not configured/, {selector: 'p'})).toBeInTheDocument()
  const box = await screen.findByLabelText('Question')
  fireEvent.change(box, {target:{value:'hello'}})
  expect(screen.getByRole('button',{name:'Send'})).toBeDisabled()
})

it('capability failure requires retry and never infers legacy', async () => {
  const client = getRkgClient()
  vi.spyOn(client,'getConversationCapabilities').mockRejectedValue(new RkgApiError(503,'unavailable','Unavailable.'))
  const history = vi.spyOn(client,'getConversation')
  renderAsk('/conversations/conv-orders-demo')
  expect(await screen.findByRole('button',{name:'Reload conversation'})).toBeInTheDocument()
  fireEvent.change(screen.getByLabelText('Question'),{target:{value:'hello'}})
  expect(screen.getByRole('button',{name:'Send'})).toBeDisabled()
  expect(history).not.toHaveBeenCalled()
  expect(screen.queryByText(/Legacy backend:/)).not.toBeInTheDocument()
})

it('404 capabilities uses legacy request without locale or unavailable query', async () => {
  const client = getRkgClient()
  vi.spyOn(client,'getConversationCapabilities').mockRejectedValue(new RkgApiError(404,'not_found','Missing.'))
  const history = vi.spyOn(client,'getConversation')
  const submit = vi.spyOn(client,'submitTurn')
  renderAsk('/conversations/conv-orders-demo')
  expect(await screen.findByText(/Legacy backend:/)).toBeInTheDocument()
  const box=screen.getByLabelText('Question')
  fireEvent.change(box,{target:{value:' hello '}})
  await waitFor(()=>expect(screen.getByRole('button',{name:'Send'})).toBeEnabled())
  fireEvent.click(screen.getByRole('button',{name:'Send'}))
  await waitFor(()=>expect(submit).toHaveBeenCalled())
  expect(submit.mock.calls[0][1].question).toBe(' hello ')
  expect(submit.mock.calls[0][1]).not.toHaveProperty('ui_locale')
  expect(history.mock.calls[0][1]).not.toHaveProperty('include_unavailable')
})

it('rejects substituted exact evidence and never falls back to entity detail', async () => {
  const client=getRkgClient()
  const entities=vi.spyOn(client,'getEntity')
  vi.spyOn(client,'getExactCitation').mockResolvedValue({schema_version:'rkg.citation/1',conversation_id:'conv-orders-demo',turn_id:'turn-orders-1',snapshot_id:'snap-orders-001',citation_index:0,evidence:{id:'another-evidence',file_path:'app/wrong.py',provenance:'source',start_line:1,end_line:2,rule:'synthetic'}})
  renderAsk('/conversations/conv-orders-demo')
  const source=await screen.findAllByRole('button',{name:'Open citation 1'})
  source[0].focus()
  fireEvent.click(source[0])
  expect(await screen.findByText('The exact cited evidence is unavailable.')).toBeInTheDocument()
  expect(screen.queryByText('app/wrong.py:1–2')).not.toBeInTheDocument()
  expect(entities).not.toHaveBeenCalled()
  fireEvent.keyDown(document,{key:'Escape'})
  await waitFor(()=>expect(source[0]).toHaveFocus())
})

it('submits a question beyond the former character ceiling', async () => {
  const client = getRkgClient()
  const submit = vi.spyOn(client, 'submitTurn')
  renderAsk('/conversations/conv-orders-demo')
  await screen.findByRole('heading', {name:'Order flow'})
  const question = 'Which functions are called? ' + 'synthetic '.repeat(3000)
  const box = screen.getByLabelText('Question')
  expect(box).not.toHaveAttribute('maxlength')
  fireEvent.change(box, {target:{value:question}})
  expect(screen.getByText(String(question.length) + ' characters')).toBeInTheDocument()
  await waitFor(() => expect(screen.getByRole('button', {name:'Send'})).toBeEnabled())
  fireEvent.click(screen.getByRole('button', {name:'Send'}))
  await waitFor(() => expect(submit).toHaveBeenCalledWith('conv-orders-demo', expect.objectContaining({question})))
  await waitFor(() => expect(box).toHaveValue(''))
})
