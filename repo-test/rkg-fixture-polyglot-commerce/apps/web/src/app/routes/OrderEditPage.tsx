import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { OrderStatus } from '@/domain/order';
import orderApi from '@/services/orderApi';
export default function OrderEditPage() {
    const { orderId = '' } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState<OrderStatus>('CREATED');
    useEffect(() => { void orderApi.getOrder(orderId).then(order => setStatus(order.status)); }, [orderId]);
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        await orderApi.updateOrder(orderId, { status });
        navigate(`/orders/${orderId}`);
    }
    return <form onSubmit={submit}><h1>Edit order {orderId}</h1><label>Status<select value={status} onChange={event => setStatus(event.target.value as OrderStatus)}>{(['CREATED', 'PAID', 'PROCESSING', 'SHIPPED', 'CANCELLED'] as const).map(value => <option key={value}>{value}</option>)}</select></label><button type="submit">Save</button></form>;
}
