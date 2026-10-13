import { Link } from 'react-router-dom';
import LoadingState from '../../components/LoadingState';
import { OrderStatusBadge } from '@/components/OrderStatusBadge';
import { useOrders } from '../../hooks/useOrders';

export default function OrdersPage() {
  const { orders, loading, error } = useOrders();
  if (loading) return <LoadingState label="Loading orders" />;
  if (error) return <p role="alert">Unable to load orders: {error}</p>;

  return (
    <><h1>Orders</h1><ul>{orders.map((order) => (
      <li key={order.id}><Link to={`/orders/${order.id}`}>{order.id}</Link>{' '}<OrderStatusBadge status={order.status} /></li>
    ))}</ul></>
  );
}
