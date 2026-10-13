// DOM-only axe checks. Browser layout/contrast/device walkthrough are separate.
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import App from '../App'
import { previewCases } from './previewClient'

afterEach(() => { cleanup(); localStorage.clear() })
const axeModule = process.env.RKG_PREVIEW_AXE_MODULE
const combinations = previewCases.flatMap(([scenario]) => ['vi', 'en'].flatMap((locale) => ['light', 'dark'].map((theme) => [scenario, locale, theme])))
describe.skipIf(!axeModule)('Ask preview automated DOM accessibility (contrast excluded)', () => {
  it.each(combinations)('%s / %s / %s has no WCAG A/AA DOM violations', async (scenario, locale, theme) => {
    localStorage.setItem('rkg-locale', locale)
    localStorage.setItem('rkg-theme', theme)
    window.location.hash = `/conversations/preview-${scenario}`
    render(<App />)
    await screen.findByRole('heading', { name: /^Ask ·/ })
    await waitFor(() => expect(document.querySelector('.ask-status')).toBeNull())
    const controls = document.querySelector<HTMLDetailsElement>('.preview-harness details')!
    controls.open = true
    const axe = await import(/* @vite-ignore */ axeModule!)
    const result = await axe.default.run(document.body, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] },
      rules: { 'color-contrast': { enabled: false } },
    })
    expect(result.violations.map((v: { id: string }) => v.id)).toEqual([])
  })
})
