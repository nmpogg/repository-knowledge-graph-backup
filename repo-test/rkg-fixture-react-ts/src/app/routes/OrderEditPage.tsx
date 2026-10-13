import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { OrderStatus } from '@/domain/order';
import orderApi from '@/services/orderApi';

export default function OrderEditPage() {
  const { orderId = '' } = useParams();
  const navigate = useNavigate();
  const [customerName, setCustomerName] = useState('');
  const [status, setStatus] = useState<OrderStatus>('pending');
  useEffect(() => { void orderApi.getOrder(orderId).then((order) => { setCustomerName(order.customerName); setStatus(order.status); }); }, [orderId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await orderApi.updateOrder(orderId, { customerName, status });
    navigate(`/orders/${orderId}`);
  }

  return <form onSubmit={submit}><h1>Edit order {orderId}</h1><label>Customer<input value={customerName} onChange={(event) => setCustomerName(event.target.value)} /></label><label>Status<select value={status} onChange={(event) => setStatus(event.target.value as OrderStatus)}><option value="pending">pending</option><option value="processing">processing</option><option value="shipped">shipped</option><option value="cancelled">cancelled</option></select></label><button type="submit">Save</button></form>;
}
