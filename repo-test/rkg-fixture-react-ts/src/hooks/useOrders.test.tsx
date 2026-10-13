import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import orderApi from '../services/orderApi';
import { useOrders } from './useOrders';

vi.mock('../services/orderApi', () => ({ default: { listOrders: vi.fn() } }));

describe('useOrders', () => {
  beforeEach(() => vi.mocked(orderApi.listOrders).mockReset());

  it('loads orders from the service', async () => {
    const orders = [{ id: 'ORD-2', customerName: 'Grace', totalCents: 2200, status: 'processing' as const }];
    vi.mocked(orderApi.listOrders).mockResolvedValue(orders);
    const { result } = renderHook(() => useOrders());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.orders).toEqual(orders);
  });
});
