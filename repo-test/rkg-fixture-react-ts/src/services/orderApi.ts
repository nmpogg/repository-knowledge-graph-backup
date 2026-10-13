import type { Order, OrderUpdate } from '../domain/order';
import { httpClient, type HttpClient } from './httpClient';

export class OrderApi {
  constructor(private readonly client: HttpClient) {}

  listOrders(): Promise<Order[]> {
    return this.client.get<Order[]>('/api/orders');
  }

  getOrder(orderId: string): Promise<Order> {
    return this.client.get<Order>(`/api/orders/${encodeURIComponent(orderId)}`);
  }

  updateOrder(orderId: string, update: OrderUpdate): Promise<Order> {
    return this.client.put<Order>(`/api/orders/${encodeURIComponent(orderId)}`, update);
  }

  checkInventory(): Promise<{ available: boolean }> {
    return fetch('https://inventory.example.test/health').then((response) => response.json());
  }
}

const orderApi = new OrderApi(httpClient);
export default orderApi;
