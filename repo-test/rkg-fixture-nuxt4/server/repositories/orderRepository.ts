import type { Order } from '#shared/types/order'

const seedOrders: readonly Order[] = [
  { id: 'ord-1001', customerName: 'Ada Lovelace', totalCents: 12900, status: 'processing', updatedAt: '2026-10-01T09:00:00Z' },
  { id: 'ord-1002', customerName: 'Grace Hopper', totalCents: 8450, status: 'shipped', updatedAt: '2026-10-02T11:30:00Z' },
]

export class OrderRepository {
  private readonly orders = new Map(seedOrders.map(order => [order.id, { ...order }]))

  findAll(): Order[] {
    return Array.from(this.orders.values(), order => ({ ...order }))
  }

  findById(orderId: string): Order | undefined {
    const order = this.orders.get(orderId)
    return order ? { ...order } : undefined
  }

  cancel(orderId: string): Order | undefined {
    const order = this.orders.get(orderId)
    if (!order) return undefined
    const cancelled: Order = { ...order, status: 'cancelled', updatedAt: '2026-10-05T00:00:00Z' }
    this.orders.set(orderId, cancelled)
    return { ...cancelled }
  }
}

export const orderRepository = new OrderRepository()
