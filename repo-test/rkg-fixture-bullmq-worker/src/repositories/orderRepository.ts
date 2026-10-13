import type { Order } from '../domain/order.js';

export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(orderId: string): Promise<Order | undefined>;
}
