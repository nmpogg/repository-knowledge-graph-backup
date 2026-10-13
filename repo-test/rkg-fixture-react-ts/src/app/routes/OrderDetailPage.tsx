import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type { Order } from '@/domain/order';
import orderApi from '../../services/orderApi';
import LoadingState from '../../components/LoadingState';
import { OrderStatusBadge } from '../../components/OrderStatusBadge';

export default function OrderDetailPage() {
  const { orderId = '' } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { orderApi.getOrder(orderId).then(setOrder, (reason: unknown) => setError(String(reason))); }, [orderId]);

  if (error) return <p role="alert">{error}</p>;
  if (!order) return <LoadingState label="Loading order" />;
  return <><h1>Order {order.id}</h1><p>{order.customerName}</p><OrderStatusBadge status={order.status} /> <Link to="edit">Edit</Link></>;
}
