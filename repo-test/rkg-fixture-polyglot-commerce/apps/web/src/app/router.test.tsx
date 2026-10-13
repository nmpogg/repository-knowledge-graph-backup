import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import orderApi from '../services/orderApi';
import { appRoutes } from './router';

vi.mock('../services/orderApi', () => ({
  default: { listOrders: vi.fn(), getOrder: vi.fn(), updateOrder: vi.fn() },
}));

describe('application routes', () => {
  beforeEach(() => vi.mocked(orderApi.getOrder).mockReset());

  it('renders the nested index route', async () => {
    render(<RouterProvider router={createMemoryRouter(appRoutes, { initialEntries: ['/'] })} />);
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
  });

  it('renders a dynamic order route inside the root layout', async () => {
    vi.mocked(orderApi.getOrder).mockResolvedValue({ id: 'ORD-42', items: [], totalCents: 4200, status: 'SHIPPED' });
    render(<RouterProvider router={createMemoryRouter(appRoutes, { initialEntries: ['/orders/ORD-42'] })} />);
    expect(await screen.findByRole('heading', { name: 'Order ORD-42' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
  });

  it('renders the catch-all route', async () => {
    render(<RouterProvider router={createMemoryRouter(appRoutes, { initialEntries: ['/missing'] })} />);
    expect(await screen.findByRole('heading', { name: 'Not found' })).toBeInTheDocument();
  });
});
