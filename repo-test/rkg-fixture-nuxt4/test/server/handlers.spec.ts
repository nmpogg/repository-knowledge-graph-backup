import type { H3Event } from 'h3'
import { describe, expect, it, vi } from 'vitest'
import { createListOrdersHandler } from '../../server/api/orders/index.get'
import { createGetOrderHandler } from '../../server/api/orders/[orderId].get'
import { createCancelOrderHandler } from '../../server/api/orders/[orderId]/cancel.post'

const event = {} as H3Event

describe('Nitro order handlers', () => {
  it('calls list service from GET /api/orders', async () => {
    const listOrders = vi.fn(() => [{ id: 'ord-list' }])
    const result = await createListOrdersHandler({ listOrders } as never)(event)
    expect(listOrders).toHaveBeenCalledOnce()
    expect(result).toEqual([{ id: 'ord-list' }])
  })

  it('reads orderId and calls get service', async () => {
    const getOrder = vi.fn((orderId: string) => ({ id: orderId }))
    const readParam = vi.fn(() => 'ord-get')
    const result = await createGetOrderHandler({ getOrder } as never, readParam)(event)
    expect(readParam).toHaveBeenCalledWith(event, 'orderId')
    expect(getOrder).toHaveBeenCalledWith('ord-get')
    expect(result).toEqual({ id: 'ord-get' })
  })

  it('reads orderId and calls cancel service', async () => {
    const cancelOrder = vi.fn((orderId: string) => ({ id: orderId, status: 'cancelled' }))
    const result = await createCancelOrderHandler({ cancelOrder } as never, () => 'ord-cancel')(event)
    expect(cancelOrder).toHaveBeenCalledWith('ord-cancel')
    expect(result).toEqual({ id: 'ord-cancel', status: 'cancelled' })
  })
})
