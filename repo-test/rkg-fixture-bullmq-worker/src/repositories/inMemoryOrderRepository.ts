import type { Order } from '../domain/order.js';
import type { OrderRepository } from './orderRepository.js';

export class InMemoryOrderRepository implements OrderRepository {
  private readonly orders = new Map<string, Order>();

  async save(order: Order): Promise<void> {
    this.orders.set(order.id, { ...order });
  }

  async findById(orderId: string): Promise<Order | undefined> {
    const order = this.orders.get(orderId);
    return order ? { ...order } : undefined;
  }
}
