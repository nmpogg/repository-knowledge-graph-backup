import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'

afterEach(() => {
  cleanup()
  localStorage.removeItem('rkg-locale')
})

describe('App', () => {
  it('renders repositories landing for newcomers', async () => {
    render(<App />)
    expect(
      await screen.findByRole('heading', { name: 'Repositories' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Explorer' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Switch to Vietnamese' })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByText('Loading repositories…')).not.toBeInTheDocument()
    })
  })

  it('switches UI copy to Vietnamese', async () => {
    render(<App />)
    await screen.findByRole('heading', { name: 'Repositories' })
    screen.getAllByRole('button', { name: 'Switch to Vietnamese' })[0]!.click()
    expect(
      await screen.findByRole('heading', { name: 'Kho mã' }),
    ).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByText('Đang tải kho mã…')).not.toBeInTheDocument()
    })
  })
})
