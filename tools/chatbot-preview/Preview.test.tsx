import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AnnouncerProvider } from '../components/ui/Announcer'
import { LocaleProvider } from '../i18n'
import { ConversationPage } from '../pages/conversations/ConversationPage'
import { previewCases } from './previewClient'

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks() })
function ask(scenario: string, locale = 'vi') {
  localStorage.setItem('rkg-locale', locale)
  return render(<LocaleProvider><AnnouncerProvider><MemoryRouter initialEntries={[`/conversations/preview-${scenario}`]}>
    <Routes><Route path="/conversations/:conversationId" element={<ConversationPage />} /></Routes>
  </MemoryRouter></AnnouncerProvider></LocaleProvider>)
}
async function ready(scenario: string, locale = 'vi') {
  const view = ask(scenario, locale)
  await screen.findByRole('heading', { name: /^Ask ·/ })
  const box = await screen.findByLabelText(locale === 'vi' ? 'Câu hỏi' : 'Question')
  if (scenario !== 'unavailable') await waitFor(() => expect(box).toBeEnabled())
  return { view, box }
}

describe('existing Ask UX prototype', () => {
  it('shows one natural answer, collapsed details and exact source with keyboard focus restoration', async () => {
    await ready('answer')
    expect(document.querySelectorAll('.preview-answer')).toHaveLength(1)
    expect(screen.getByText(/Ở bước tiếp theo/)).toBeInTheDocument()
    const details = document.querySelector('details')!
    expect(details.open).toBe(false)
    const button = screen.getByRole('button', { name: 'Mở nguồn app/api/orders.py:42' })
    button.focus(); fireEvent.click(button)
    const dialog = await screen.findByRole('dialog')
    expect(await within(dialog).findByText('app/api/orders.py:42')).toBeInTheDocument()
    expect(within(dialog).queryByText(/app\/services\/orders.py/)).not.toBeInTheDocument()
    expect(within(dialog).getByText(/snap-orders/)).toBeInTheDocument()
    const close = within(dialog).getByRole('button', { name: 'Đóng' })
    expect(close).toHaveFocus()
    fireEvent.keyDown(document, { key: 'Tab' }); expect(close).toHaveFocus()
    fireEvent.keyDown(document, { key: 'Escape' })
    await waitFor(() => expect(button).toHaveFocus())
  })
  it('does not duplicate insufficient copy or show raw reason codes', async () => {
    await ready('missing')
    expect(screen.getAllByText(/Tôi chưa tìm thấy endpoint login/)).toHaveLength(1)
    expect(screen.queryByText('Snapshot này không đủ bằng chứng.')).not.toBeInTheDocument()
    expect(document.body.textContent).not.toContain('max_chars')
  })
  it.each(['partial', 'legacy'])('retains %s coverage annotation on remount from the fixture catalog', async (scenario) => {
    let current = await ready(scenario)
    const pattern = scenario === 'partial' ? /bao phủ một phần/ : /Chưa xác định được mức độ bao phủ/
    expect(screen.getByText(pattern)).toBeInTheDocument()
    current.view.unmount()
    current = await ready(scenario)
    expect(screen.getByText(pattern)).toBeInTheDocument()
  })
  it('resumes the original calls intent after selecting a clarification candidate', async () => {
    await ready('clarify')
    fireEvent.click(screen.getByRole('button', { name: /1\. Endpoint/ }))
    expect(await screen.findByText(/Bạn đã chọn GET/)).toHaveTextContent('gọi trực tiếp load_order')
    expect(screen.queryByRole('button', { name: /1\. Endpoint/ })).not.toBeInTheDocument()
  })
  it.each(['disabled', 'timeout', 'conflict'])('keeps draft and pending controls for %s', async (scenario) => {
    const { box } = await ready(scenario)
    fireEvent.change(box, { target: { value: 'bản nháp kiểm tra' } })
    fireEvent.click(screen.getByRole('button', { name: 'Gửi' }))
    expect(screen.getByRole('button', { name: 'Đang hỏi…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: /^Xóa / })).toBeDisabled()
    if (scenario === 'conflict') await screen.findByRole('button', { name: 'Tải lại hội thoại' }, { timeout: 3000 })
    else await screen.findByRole('alert', {}, { timeout: 3000 })
    expect(box).toHaveValue('bản nháp kiểm tra')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Gửi' })).toBeEnabled())
  })
  it('disables send and citation for unavailable snapshot while retaining transcript', async () => {
    const { box } = await ready('unavailable')
    await waitFor(() => expect(box).toBeDisabled())
    expect(screen.getByText(/Ở bước tiếp theo/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gửi' })).toBeDisabled()
  })
  it('renders model-like HTML as escaped text', async () => {
    await ready('safe')
    const answer = screen.getByText(/<script>alert/)
    expect(answer.querySelector('script')).toBeNull()
    expect(answer.innerHTML).toContain('&lt;script&gt;')
  })
  it('keeps fixture answer language independent from interface locale', async () => {
    await ready('greeting', 'en')
    expect(screen.getByText(/Chào bạn!/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Open source/ })).not.toBeInTheDocument()
  })
  it.each(previewCases)('has no runtime fetch in %s fixture flow', async (scenario) => {
    const fetch = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network forbidden in preview'))
    await ready(scenario)
    expect(fetch).not.toHaveBeenCalled()
  })
})
