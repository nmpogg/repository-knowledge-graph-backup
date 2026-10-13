import { describe, expect, it, vi } from 'vitest'
import { OrderRepository } from '../../server/repositories/orderRepository'
import { fetchInventoryStatus, OrderNotFoundError, OrderService } from '../../server/services/orderService'

describe('OrderService', () => {
  it('delegates list, get, and cancel operations to the repository', () => {
    const service = new OrderService(new OrderRepository())
    expect(service.listOrders()).toHaveLength(2)
    expect(service.getOrder('ord-1001').id).toBe('ord-1001')
    expect(service.cancelOrder('ord-1001').status).toBe('cancelled')
    expect(() => service.getOrder('missing')).toThrow(OrderNotFoundError)
  })

  it('uses the static external inventory endpoint through an injected fetcher', async () => {
    const fetcher = vi.fn(async () => ({ available: true }))
    await expect(fetchInventoryStatus(fetcher)).resolves.toEqual({ available: true })
    expect(fetcher).toHaveBeenCalledWith('https://inventory.example.test/availability')
  })
})
