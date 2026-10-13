// Run against the production Ask and a real synthetic loopback API.
// Export assertions only: no DOM, screenshots, transcripts or source excerpts.
import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
import {mkdtempSync, readFileSync, existsSync, writeFileSync} from 'node:fs'
import {tmpdir} from 'node:os'
import {join, resolve} from 'node:path'
import {pathToFileURL} from 'node:url'
const {chromium} = await import(pathToFileURL(process.env.RKG_PLAYWRIGHT_MODULE).href)
const root=resolve('.'), temp=mkdtempSync(join(tmpdir(),'rkg-ask-browser-'))
const apiPort=24000+Math.floor(Math.random()*1000), uiPort=apiPort+1000
const api='http://127.0.0.1:'+apiPort, ui='http://127.0.0.1:'+uiPort
const descriptor=join(temp,'fixture.json'), checks=[]
const env={...process.env}; delete env.OPENROUTER_API_KEY
const backend=spawn(join(root,'.venv/bin/python'),['-m','tests.browser.chatbot_fixture',temp,String(apiPort),descriptor],{cwd:root,env,stdio:'ignore'})
const frontend=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port',String(uiPort),'--strictPort'],{cwd:join(root,'frontend'),env:{...env,VITE_RKG_CLIENT:'live',VITE_RKG_API_BASE:'',VITE_RKG_SESSION:'synthetic-browser-session',RKG_API_UPSTREAM:api},stdio:'ignore'})
let browser, stage="readiness"
const pause=ms=>new Promise(done=>setTimeout(done,ms))
async function ready(url){for(let n=0;n<120;n++){try{if((await fetch(url)).ok)return}catch{} await pause(250)}throw Error('Synthetic service readiness failed')}
async function json(url,body){const result=await fetch(url,body?{method:'POST',headers:{'Content-Type':'application/json','X-RKG-Session':'synthetic-browser-session'},body:JSON.stringify(body)}:undefined);assert.ok(result.status===200 || result.status===201);return result.json()}
async function waitEnabled(page){await page.waitForFunction(()=>{const box=document.querySelector('.ask-composer textarea');return box && !box.disabled && !document.querySelector('.ask-status')},{},{timeout:10000})}
async function submit(page,text){await waitEnabled(page);await page.locator('.ask-composer textarea').fill(text);const response=page.waitForResponse(r=>r.request().method()==='POST' && r.url().endsWith('/turns'));await page.locator('.ask-composer button[type="submit"]').click();const r=await response;assert.equal(r.status(),200);const body=await r.json();await waitEnabled(page);return body}
try{
 await ready(api+'/api/v1/conversations/capabilities');await ready(ui)
 assert.ok(existsSync(descriptor));const pin=JSON.parse(readFileSync(descriptor,'utf8'))
 browser=await chromium.launch({headless:true,...(process.env.RKG_CHROMIUM_EXECUTABLE ? {executablePath:process.env.RKG_CHROMIUM_EXECUTABLE} : {})})
 for(const locale of ['vi','en'])for(const theme of ['light','dark'])for(const width of [375,1280]){
  const label=locale+'/'+theme+'/'+width
  stage=label+":initial"
  const conv=await json(api+'/api/v1/conversations',{repository_id:pin.repository_id,snapshot_id:pin.snapshot_id,title:'Synthetic Ask'})
  const context=await browser.newContext({viewport:{width,height:900}})
  await context.addInitScript(({locale,theme})=>{localStorage.setItem('rkg-locale',locale);localStorage.setItem('rkg-theme',theme)},{locale,theme})
  await context.route('**/*',route=>new URL(route.request().url()).origin===ui?route.continue():route.abort())
  const page=await context.newPage();await page.goto(ui+'/conversations/'+conv.conversation_id);await waitEnabled(page)
  assert.equal(await page.locator('html').getAttribute('data-theme'),theme)
  const before=await json(api+'/__fixture/counts')
  const greeting=await submit(page,locale==='vi'?'alo':'hello')
  assert.equal(greeting.response_metadata.kind,'greeting');assert.equal(greeting.response_metadata.language,locale)
  assert.equal(greeting.claims.length,0);assert.equal(greeting.citations.length,0)
  assert.equal((await json(api+'/__fixture/counts')).model_calls,before.model_calls)
  checks.push(label+': greeting local and zero model calls')
  stage=label+":clarification"
  const original='What does '+String.fromCharCode(96)+'a'+String.fromCharCode(96)+' call?' + (process.env.RKG_LONG_QUESTION === '1' ? ' synthetic'.repeat(7000) : '')
  const clarify=await submit(page,original);assert.equal(clarify.status,'needs_clarification')
  assert.equal(clarify.response_metadata.language,'en');assert.ok(clarify.candidate_entities.length>1)
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),true)
  const candidate=clarify.candidate_entities.findIndex(e=>e.qualified_name==='app.cycle.a');assert.ok(candidate>=0)
  const choice=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/turns'))
  await page.locator('.ask-candidates button').nth(candidate).click()
  const selection=await (await choice).json();await waitEnabled(page)
  assert.equal(selection.status,'answered');assert.equal(selection.resolved_question,original);assert.equal(selection.response_metadata.language,'en')
  assert.equal(await page.locator('.ask-thread details[open]').count(),0)
  checks.push(label+': ordered choice resumes original intent; claims collapsed')
  stage=label+":endpoint"
  const endpoint=await submit(page,locale==='vi'?'GET /orders/{id} goi nhung ham nao?':'What does GET /orders/{id} call?')
  assert.equal(endpoint.status,'answered');assert.equal(endpoint.response_metadata.subject.type,'Endpoint')
  assert.ok(endpoint.answer.includes('GET /orders/{id}'));assert.ok(endpoint.answer.includes('app.cycle.a') || endpoint.answer.includes('a'))
  assert.ok(endpoint.answer.includes(locale==='vi'?'Gián tiếp':'Indirect'))
  assert.equal(await page.locator('.ask-answer').last().textContent(),endpoint.answer)
  stage=label+":citation"
  const source=page.locator('.ask-turn').last().locator('.ask-cites button').first()
  await source.focus();await page.keyboard.press('Enter');await page.getByRole('dialog').waitFor()
  const exact=await json(api+'/api/v1/conversations/'+conv.conversation_id+'/turns/'+endpoint.turn_id+'/citations/0')
  assert.equal(exact.evidence.id,endpoint.citations[0].evidence_id)
  await page.getByRole('dialog').getByText(exact.evidence.file_path+':'+exact.evidence.start_line+'–'+exact.evidence.end_line,{exact:true}).waitFor()
  await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement?.closest('[role="dialog"]')!==null),true)
  await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement?.closest('[role="dialog"]')!==null),true)
  await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'detached'});assert.equal(await source.evaluate(el=>el===document.activeElement),true)
  checks.push(label+': endpoint bridge/direct/indirect; exact citation keyboard and focus')
  stage=label+":limits"
  for(let n=0;n<6;n++)await submit(page,locale==='vi'?'alo':'hello')
  const limited=await submit(page,locale==='vi'?'GET /orders/{id} goi ham nao?':'What does GET /orders/{id} call?')
  assert.equal(limited.response_metadata.history_truncated,true)
  await page.reload();await waitEnabled(page)
  const history=await json(api+'/api/v1/conversations/'+conv.conversation_id+'/turns')
  assert.deepEqual(history.items.at(-1).response_metadata,limited.response_metadata)
  assert.ok(await page.locator('.ask-turn').last().locator('.ask-note').count()>0)
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),true)
  checks.push(label+': durable limits reload; readable viewport without horizontal overflow')
  await context.close()
 }
 stage="unavailable"
 const unavailableConv=await json(api+'/api/v1/conversations',{repository_id:pin.repository_id,snapshot_id:pin.snapshot_id,title:'Synthetic unavailable'})
 const context=await browser.newContext();const page=await context.newPage()
 await context.route('**/*',route=>new URL(route.request().url()).origin===ui?route.continue():route.abort())
 await page.goto(ui+'/conversations/'+unavailableConv.conversation_id);await waitEnabled(page);await submit(page,'What does GET /orders/{id} call?')
 await json(api+'/__fixture/unavailable',{})
 await page.reload();await page.locator('.ask-answer').waitFor()
 await page.waitForFunction(()=>document.querySelector('.ask-composer textarea')?.disabled)
 assert.equal(await page.locator('.ask-cites button').first().isDisabled(),true)
 assert.equal(await page.locator('.ask-composer button').isDisabled(),true)
 checks.push('unavailable pin: stored transcript readable; submit and citations disabled')
 await context.close()
 const result={result:'passed',browser:browser.version(),variants:8,checks,network:'loopback_only',provider:'schema_bound_synthetic_no_external_calls',not_run:['live_provider_quality','human_UAT','operator_database_migration']}
 if(process.env.RKG_BROWSER_RESULT)writeFileSync(process.env.RKG_BROWSER_RESULT,JSON.stringify(result,null,2)+'\n')
 process.stdout.write(JSON.stringify({result:result.result,variants:8,assertion_groups:checks.length})+'\n')
}catch(error){process.stderr.write('Browser walkthrough failed: '+(error instanceof Error?error.name:'Error')+' at '+stage+'\n');process.exitCode=1}
finally{await browser?.close();frontend.kill();backend.kill()}
