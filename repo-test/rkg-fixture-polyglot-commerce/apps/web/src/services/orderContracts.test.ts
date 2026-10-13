import { describe, expect, it, vi } from 'vitest';
import { OrderApi } from './orderApi';
import type { HttpClient } from './httpClient';
import type { OrderRequest } from '../domain/order';
describe('Spring-compatible method, path and body', () => {
    it('creates an order using POST and updates status using PATCH', async () => {
        const client: HttpClient = { get: vi.fn(), post: vi.fn().mockResolvedValue({ id: 'order-1' }), patch: vi.fn().mockResolvedValue({ id: 'order-1' }) };
        const api = new OrderApi(client);
        const request: OrderRequest = { items: [{ sku: 'SKU-1', quantity: 1, unitPriceCents: 500 }] };
        await api.createOrder(request);
        expect(client.post).toHaveBeenCalledWith('/api/orders', request);
        await api.updateOrder('order-1', { status: 'PAID' });
        expect(client.patch).toHaveBeenCalledWith('/api/orders/order-1/status', { status: 'PAID' });
    });
});
