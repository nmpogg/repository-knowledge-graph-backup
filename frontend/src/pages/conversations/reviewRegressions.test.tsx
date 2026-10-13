import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { AnnouncerProvider } from '../../components/ui/Announcer'
import { LocaleProvider } from '../../i18n'
import { translate } from '../../i18n/locale'
import { getRkgClient } from '../../client'
import { ConversationPage } from './ConversationPage'
import { TurnReply } from './TurnReply'
import { readResponseMetadata } from './responseMetadata'
import type { ConversationTurn, ExactCitation, TurnSubmitResult } from '../../types/api'

afterEach(() => { vi.restoreAllMocks(); cleanup(); localStorage.removeItem('rkg-locale') })
function ask() {
  return render(<LocaleProvider><AnnouncerProvider><MemoryRouter initialEntries={['/conversations/conv-orders-demo']}><Link to="/conversations/synthetic-other">Switch synthetic conversation</Link><Routes><Route path="/conversations/:conversationId" element={<ConversationPage />} /></Routes></MemoryRouter></AnnouncerProvider></LocaleProvider>)
}
async function source(path: string, mutate?: (detail: ExactCitation)=>void) {
  const detail: ExactCitation = {schema_version:'rkg.citation/1',conversation_id:'conv-orders-demo',turn_id:'turn-orders-1',snapshot_id:'snap-orders-001',citation_index:0,evidence:{id:'ev-orders',file_path:path,provenance:'source',start_line:1,end_line:2,rule:'synthetic'}}
  mutate?.(detail)
  vi.spyOn(getRkgClient(), 'getExactCitation').mockResolvedValue(detail)
  ask()
  const button = await screen.findByRole('button',{name:'Open citation 1'})
  fireEvent.click(button)
  await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument())
}
it('accepts a normal relative source path', async () => {
  await source('src/routes.ts')
  expect(await screen.findByText('src/routes.ts:1–2')).toBeInTheDocument()
})
it.each(['conversation','turn','pin','index','evidence','absolute','traversal','source-lines','filesystem-lines'])('rejects exact citation mismatch %s without entity fallback', async (kind) => {
  const entities=vi.spyOn(getRkgClient(),'getEntity')
  await source('app/models.py',(detail)=>{
    if(kind==='conversation') detail.conversation_id='synthetic-other'
    if(kind==='turn') detail.turn_id='synthetic-other'
    if(kind==='pin') detail.snapshot_id='synthetic-other'
    if(kind==='index') detail.citation_index=1
    if(kind==='evidence') detail.evidence.id='synthetic-other'
    if(kind==='absolute') detail.evidence.file_path='/synthetic/models.py'
    if(kind==='traversal') detail.evidence.file_path='../models.py'
    if(kind==='source-lines') detail.evidence.start_line=0
    if(kind==='filesystem-lines') detail.evidence.provenance='filesystem'
  })
  expect(await screen.findByText('The exact cited evidence is unavailable.')).toBeInTheDocument()
  expect(entities).not.toHaveBeenCalled()
})
it('keeps transcript readable when snapshot is unavailable',async()=>{
  const client=getRkgClient()
  const seed=await client.getConversation('conv-orders-demo')
  vi.spyOn(client,'getConversation').mockResolvedValue({...seed,snapshot_available:false})
  ask()
  await screen.findByText(seed.turns.items[0].answer!)
  expect(screen.getByRole('button',{name:'Open citation 1'})).toBeDisabled()
  expect(screen.getByLabelText('Question')).toBeDisabled()
  expect(screen.getByRole('button',{name:'Send'})).toBeDisabled()
})
it('rejects an embedded control character', async () => {
  await source('app/a\nb.py')
  expect(await screen.findByText('The exact cited evidence is unavailable.')).toBeInTheDocument()
})
it('marks known v1 unknown coverage explicitly', () => {
  const metadata = {version:1, language:'en', kind:'insufficient',subject:null,coverage:'unknown',retrieval_truncated:null,history_truncated:null,limitations:[],insufficient_reason:'entity_not_found'}
  expect(readResponseMetadata(metadata)).not.toBeNull()
  const turn: ConversationTurn = {turn_id:'synthetic',sequence:1,status:'insufficient_evidence',question:'synthetic',resolved_question:null,answer:'Synthetic answer.',claims:[],citations:[],context_turn_ids:[],error_code:null,response_metadata:readResponseMetadata(metadata)}
  render(<TurnReply turn={turn} t={(key,params)=>translate('en',key,params)} unavailable={false} legacy={false} onSource={()=>{}} />)
  expect(screen.getByText('Coverage is unknown for this stored turn.')).toBeInTheDocument()
})
it('ignores completed submit from previous conversation', async () => {
  const client = getRkgClient()
  const seed = await client.getConversation('conv-orders-demo')
  const history = vi.spyOn(client,'getConversation').mockImplementation(async (id) => ({...structuredClone(seed),conversation:{...seed.conversation,conversation_id:id,title:id==='synthetic-other'?'Synthetic other':'Order flow'}}))
  let resolve!: (value: TurnSubmitResult)=>void
  vi.spyOn(client,'submitTurn').mockImplementation(()=>new Promise((done)=>{resolve=done}))
  ask()
  await screen.findByRole('heading',{name:'Order flow'})
  const box=screen.getByLabelText('Question')
  fireEvent.change(box,{target:{value:'synthetic pending'}})
  await waitFor(()=>expect(screen.getByRole('button',{name:'Send'})).toBeEnabled())
  fireEvent.click(screen.getByRole('button',{name:'Send'}))
  await waitFor(()=>expect(resolve).toBeDefined())
  fireEvent.click(screen.getByRole('link',{name:'Switch synthetic conversation'}))
  await screen.findByRole('heading',{name:'Synthetic other'})
  const callCount=history.mock.calls.length
  await act(async () => { resolve({...seed.turns.items[0],schema_version:'rkg.turn/1',conversation_id:'conv-orders-demo',repository_id:seed.conversation.repository_id,snapshot_id:seed.conversation.snapshot_id,revision:3,candidate_entities:[],limitations:[],retrieval_truncated:false,history_truncated:false,usage:null}); await Promise.resolve() })
  expect(history.mock.calls.length).toBe(callCount)
  await waitFor(()=>expect(screen.getByRole('heading',{name:'Synthetic other'})).toBeInTheDocument())
})
it.each(['delayed', 'failed'])('blocks previous candidates while destination history is %s', async (kind) => {
  const client = getRkgClient()
  const seed = await client.getConversation('conv-orders-demo')
  const oldCandidate = {id:'synthetic-A-root', type:'function' as const, name:'old', qualified_name:'synthetic.old', snapshot_id:seed.conversation.snapshot_id, file_path:'synthetic.py', start_line:1, end_line:2}
  let resolve!: (history: typeof seed) => void
  let reject!: (reason: Error) => void
  const next = new Promise<typeof seed>((done, fail) => {resolve=done;reject=fail})
  const history = vi.spyOn(client,'getConversation').mockImplementation(async(id) => id==='synthetic-other' ? next : {...seed, candidate_entities:[oldCandidate]})
  const submits = vi.spyOn(client,'submitTurn')
  ask()
  const oldButton = await screen.findByRole('button',{name:/Candidate 1.*synthetic.old/})
  fireEvent.click(screen.getByRole('link',{name:'Switch synthetic conversation'}))
  await waitFor(()=>expect(history).toHaveBeenCalledWith('synthetic-other',expect.anything()))
  if (kind==='failed') { await act(async()=>{reject(new Error('Synthetic history failure'))}) }
  const retained = screen.queryByRole('button',{name:/Candidate 1.*synthetic.old/})
  expect(!retained || retained.hasAttribute('disabled')).toBe(true)
  fireEvent.click(oldButton)
  expect(submits).not.toHaveBeenCalled()
  expect(screen.getByRole('button',{name:'Send'})).toBeDisabled()
  if (kind==='delayed') {
    await act(async()=>{resolve({...seed,conversation:{...seed.conversation,conversation_id:'synthetic-other',title:'Synthetic other'},candidate_entities:[]})})
    await screen.findByRole('heading',{name:'Synthetic other'})
  }
})
