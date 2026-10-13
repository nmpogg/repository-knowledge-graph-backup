import type { ProcessOrderJobData } from '../domain/jobs.js';
import type { Order } from '../domain/order.js';
import type { OrderRepository } from '../repositories/orderRepository.js';

export class OrderService {
  constructor(private readonly repository: OrderRepository) {}

  async processOrder(data: ProcessOrderJobData): Promise<Order> {
    const order: Order = {
      id: data.orderId,
      customerId: data.customerId,
      totalCents: data.totalCents,
      status: 'processed',
    };
    await this.repository.save(order);
    return order;
  }
}
