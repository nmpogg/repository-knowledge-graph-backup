import { expect, it } from 'vitest'
import { createLiveClient } from './liveClient'
import { mapTurn } from './mapWire'

it('maps durable metadata and interrupted history without pretending complete', () => {
  const turn = mapTurn({status:'interrupted', response_metadata:{version:2,coverage:'complete'}})
  expect(turn.status).toBe('interrupted')
  expect(turn.response_metadata).toBeNull()
  const metadata={version:1,language:'en',kind:'greeting',subject:null,coverage:'not_applicable',retrieval_truncated:null,history_truncated:false,limitations:[],insufficient_reason:null}
  expect(mapTurn({status:'answered',response_metadata:metadata}).response_metadata).toEqual(metadata)
})

it('calls the exact per-turn citation route and opt-in history explicitly', async () => {
  const urls: string[]=[]
  const client=createLiveClient({baseUrl:'http://127.0.0.1:8000', fetchImpl:async (input)=> {
    urls.push(String(input))
    return new Response(JSON.stringify({items:[],offset:0,limit:20,total:0,conversation:{}}), {status:200,headers:{'Content-Type':'application/json'}})
  }})
  await client.getExactCitation('conv/id','turn/id',2)
  await client.getConversation('conv/id',{include_unavailable:true})
  expect(urls[0]).toContain('/conversations/conv%2Fid/turns/turn%2Fid/citations/2')
  expect(urls[1]).toContain('include_unavailable=true')
  expect(urls.some((url)=>url.includes('/entities/'))).toBe(false)
})
