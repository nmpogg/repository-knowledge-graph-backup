import { describe, expect, it, vi } from 'vitest'
import { useOrders, type OrdersFetcher } from '../../app/composables/useOrders'
import type { Order } from '#shared/types/order'

describe('useOrders', () => {
  it('loads orders through the injected fetch boundary', async () => {
    const fixture: Order[] = [{
      id: 'ord-test', customerName: 'Test Customer', totalCents: 500,
      status: 'pending', updatedAt: '2026-10-05T00:00:00Z',
    }]
    const fetcher = vi.fn(async () => fixture) as OrdersFetcher
    const state = useOrders(fetcher)

    await state.load()

    expect(fetcher).toHaveBeenCalledWith('/api/orders')
    expect(state.orders.value).toEqual(fixture)
    expect(state.error.value).toBeNull()
    expect(state.pending.value).toBe(false)
  })

  it('exposes a safe error without leaking the fetch failure', async () => {
    const fetcher = vi.fn(async () => { throw new Error('RKG_TEST_SECRET_DO_NOT_PERSIST') }) as OrdersFetcher
    const state = useOrders(fetcher)

    await state.load()

    expect(state.orders.value).toEqual([])
    expect(state.error.value).toBe('Unable to load orders')
    expect(state.error.value).not.toContain('RKG_TEST_SECRET_DO_NOT_PERSIST')
  })
})
