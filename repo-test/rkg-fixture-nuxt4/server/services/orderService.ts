import type { Order } from '#shared/types/order'
import { orderRepository, type OrderRepository } from '../repositories/orderRepository'

export class OrderNotFoundError extends Error {
  constructor(orderId: string) {
    super(`Order not found: ${orderId}`)
    this.name = 'OrderNotFoundError'
  }
}

export class OrderService {
  constructor(private readonly repository: OrderRepository) {}

  listOrders(): Order[] {
    return this.repository.findAll()
  }

  getOrder(orderId: string): Order {
    const order = this.repository.findById(orderId)
    if (!order) throw new OrderNotFoundError(orderId)
    return order
  }

  cancelOrder(orderId: string): Order {
    const order = this.repository.cancel(orderId)
    if (!order) throw new OrderNotFoundError(orderId)
    return order
  }
}

export type InventoryFetcher = <T>(url: string) => Promise<T>

export function fetchInventoryStatus(fetcher: InventoryFetcher) {
  return fetcher<{ available: boolean }>('https://inventory.example.test/availability')
}

export const orderService = new OrderService(orderRepository)
