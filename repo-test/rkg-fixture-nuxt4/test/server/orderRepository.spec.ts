import { describe, expect, it } from 'vitest'
import { OrderRepository } from '../../server/repositories/orderRepository'

describe('OrderRepository', () => {
  it('returns deterministic copies and cancels an existing order', () => {
    const repository = new OrderRepository()
    const first = repository.findAll()
    first[0]!.customerName = 'Changed outside repository'

    expect(repository.findById('ord-1001')?.customerName).toBe('Ada Lovelace')
    expect(repository.cancel('ord-1001')?.status).toBe('cancelled')
    expect(repository.findById('missing')).toBeUndefined()
  })
})
