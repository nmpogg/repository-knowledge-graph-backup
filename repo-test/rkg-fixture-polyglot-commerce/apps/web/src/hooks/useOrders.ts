import { useEffect, useState } from 'react';
import type { Order } from '../domain/order';
import orderApi from '../services/orderApi';

interface OrdersState {
  orders: Order[];
  loading: boolean;
  error: string | null;
}

export function useOrders(): OrdersState {
  const [state, setState] = useState<OrdersState>({ orders: [], loading: true, error: null });

  useEffect(() => {
    let active = true;
    orderApi.listOrders().then(
      (orders) => active && setState({ orders, loading: false, error: null }),
      (error: unknown) => active && setState({ orders: [], loading: false, error: String(error) }),
    );
    return () => { active = false; };
  }, []);

  return state;
}
