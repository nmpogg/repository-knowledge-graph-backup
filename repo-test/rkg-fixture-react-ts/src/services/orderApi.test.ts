import { describe, expect, it, vi } from 'vitest';
import type { HttpClient } from './httpClient';
import { OrderApi } from './orderApi';

describe('OrderApi', () => {
  it('loads orders through the injected HTTP client without using the network', async () => {
    const orders = [{ id: 'ORD-1', customerName: 'Ada', totalCents: 1250, status: 'pending' as const }];
    const client: HttpClient = { get: vi.fn().mockResolvedValue(orders), put: vi.fn() };
    await expect(new OrderApi(client).listOrders()).resolves.toEqual(orders);
    expect(client.get).toHaveBeenCalledWith('/api/orders');
  });
});
