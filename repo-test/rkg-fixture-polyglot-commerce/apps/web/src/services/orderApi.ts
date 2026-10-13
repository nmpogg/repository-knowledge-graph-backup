import type { Order, OrderUpdate, OrderRequest } from '../domain/order';
import { httpClient, type HttpClient } from './httpClient';

export class OrderApi {
  constructor(private readonly client: HttpClient) {}

  // RKG_EXPECT: web-create-order
  createOrder(request: OrderRequest): Promise<Order> {
    return this.client.post<Order>('/api/orders', request);
  }

  // RKG_EXPECT: web-list-orders
  listOrders(): Promise<Order[]> {
    return this.client.get<Order[]>('/api/orders');
  }

  getOrder(orderId: string): Promise<Order> {
    return this.client.get<Order>(`/api/orders/${encodeURIComponent(orderId)}`);
  }

  updateOrder(orderId: string, update: OrderUpdate): Promise<Order> {
    return this.client.patch<Order>(`/api/orders/${encodeURIComponent(orderId)}/status`, update);
  }

  checkInventory(): Promise<{ available: boolean }> {
    return fetch('https://inventory.example.test/health').then((response) => response.json());
  }
}

const orderApi = new OrderApi(httpClient);
export default orderApi;
