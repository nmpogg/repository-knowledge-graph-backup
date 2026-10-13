// Author browser checks against synthetic preview only. Never export DOM/transcripts.
import { readFile, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { pathToFileURL } from 'node:url'

const { chromium } = await import(pathToFileURL('/tmp/rkg-chatbot-browser-checks/node_modules/playwright/index.mjs').href)
const axePath = '/tmp/rkg-chatbot-a11y-checks/node_modules/axe-core/axe.js'
const manifestPath = '.aide/generated/ui-mocks/chatbot-002/manifest.json'
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex')
const cases = ['answer', 'answer-en', 'clarify', 'missing', 'relation', 'partial', 'legacy', 'greeting', 'english', 'empty', 'disabled', 'timeout', 'conflict', 'unavailable', 'safe', 'long']
const results = []
const failures = []
const browser = await chromium.launch({ headless: true })
const combinations = [375, 768, 1024, 1440].flatMap((width) => ['vi', 'en'].flatMap((locale) => ['light', 'dark'].map((theme) => ({ width, locale, theme }))))
let index = 0
try {
  await Promise.all(Array.from({ length: 4 }, async () => {
    while (index < combinations.length) {
      const combo = combinations[index++]
      const context = await browser.newContext({ viewport: { width: combo.width, height: 900 }, reducedMotion: 'reduce' })
      await context.addInitScript(({ locale, theme }) => {
        localStorage.setItem('rkg-locale', locale)
        localStorage.setItem('rkg-theme', theme)
      }, combo)
      const page = await context.newPage()
      const unexpectedNetwork = []
      await page.route('**/*', async (route) => {
        const url = new URL(route.request().url())
        if (url.origin !== 'http://127.0.0.1:5174' || url.pathname.startsWith('/api/')) {
          unexpectedNetwork.push('non_preview_request')
          await route.abort()
        } else await route.continue()
      })
      for (const scenario of cases) {
        await page.goto(`http://127.0.0.1:5174/#/conversations/preview-${scenario}`)
        await page.locator('.ask-top h1').filter({ hasText: /^Ask ·/ }).waitFor()
        await page.waitForFunction(() => !document.querySelector('.ask-status'))
        await page.addScriptTag({ path: axePath })
        const check = await page.evaluate(async () => {
          const axe = await window.axe.run(document.body, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } })
          const violations = axe.violations.map(({ id, impact, nodes }) => ({ id, impact, targets: nodes.map(({ target }) => target) }))
          const invisible = (e) => e.getClientRects().length === 0
          const overflow = [...document.querySelectorAll('.preview-answer, .ask-cites .btn, .ask-candidates .btn, .ask-field textarea, .ask-context, .preview-details summary')].filter((e) => !invisible(e)).filter((e) => {
            const r = e.getBoundingClientRect()
            return r.left < -1 || r.right > innerWidth + 1 || e.scrollWidth > e.clientWidth + 1
          }).map((e) => e.className || e.tagName)
          const send = document.querySelector('.ask-composer button').getBoundingClientRect()
          return { violations, overflow, documentOverflow: document.documentElement.scrollWidth > innerWidth + 1, composerVisible: send.bottom <= innerHeight + 1 && send.top >= 0 }
        })
        const row = { ...combo, scenario, ...check, network: unexpectedNetwork.length ? 'failed' : 'passed' }
        results.push(row)
        if (check.violations.length || check.overflow.length || check.documentOverflow || !check.composerVisible || unexpectedNetwork.length) failures.push(row)
        if (['disabled', 'timeout', 'conflict'].includes(scenario)) {
          const question = page.locator('#ask-question')
          await question.fill('Kiểm tra preview')
          await page.locator('.ask-composer button').click()
          const pendingGuard = await page.locator('.ask-composer button').isDisabled() && await page.locator('.ask-delete').isDisabled()
          await page.waitForFunction(() => !document.querySelector('.ask-status'))
          const state = await page.evaluate(async () => {
            const audit = await window.axe.run(document.body, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } })
            return { violations: audit.violations.map(({ id, impact, nodes }) => ({ id, impact, targets: nodes.map(({ target }) => target) })) }
          })
          const draftKept = await question.inputValue() === 'Kiểm tra preview'
          const row = { ...combo, scenario: `${scenario}-submitted`, ...state, pendingGuard, draftKept }
          results.push(row)
          if (state.violations.length || !pendingGuard || !draftKept) failures.push(row)
        }
      }
      await context.close()
      console.log(`Checked width=${combo.width} locale=${combo.locale} theme=${combo.theme}`)
    }
  }))
  // Real keyboard activation, trapped focus, Escape and source-button focus restore.
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://127.0.0.1:5174/#/conversations/preview-answer')
  const source = page.getByRole('button', { name: /(?:Open source|Mở nguồn) app\/api\/orders.py:42/ })
  await source.focus()
  await page.keyboard.press('Enter')
  const dialog = page.getByRole('dialog')
  await dialog.waitFor()
  await dialog.getByText('app/api/orders.py:42', { exact: true }).waitFor()
  await page.addScriptTag({ path: axePath })
  const dialogViolations = await page.evaluate(async () => (await window.axe.run(document.body, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] },
  })).violations.map(({ id, impact, nodes }) => ({ id, impact, targets: nodes.map(({ target }) => target) })))
  if (dialogViolations.length) failures.push({ check: 'source_dialog_a11y', violations: dialogViolations })
  const close = dialog.getByRole('button')
  const closeFocused = await close.evaluate((e) => e === document.activeElement)
  await page.keyboard.press('Tab')
  const trapped = await close.evaluate((e) => e === document.activeElement)
  await page.keyboard.press('Escape')
  const restored = await source.evaluate((e) => e === document.activeElement)
  const keyboard = { activation: 'passed', closeFocused, trapped, restored, dialogViolations }
  if (!closeFocused || !trapped || !restored) failures.push({ check: 'keyboard_dialog', ...keyboard })
  await page.close()
  const report = {
    kind: 'author_browser_checks', fixture_only: true,
    preview_manifest_sha256: hash(await readFile(manifestPath)),
    checker_sha256: hash(await readFile(new URL(import.meta.url))),
    axe_sha256: hash(await readFile(axePath)), browser_version: browser.version(),
    count: results.length, keyboard, failures, results,
    limits: ['Automated Chromium checks; human primary-device walkthrough is separately attested.', 'No live API/provider/grounding/persistence verification.'],
  }
  await writeFile('/tmp/rkg-chatbot-browser-results.json', JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify({ checks: results.length, failures: failures.length, keyboard }))
  if (failures.length) process.exitCode = 1
} finally { await browser.close() }
