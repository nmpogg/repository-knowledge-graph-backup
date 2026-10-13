import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import orderApi from '@/services/orderApi';
export default function CreateOrderPage() {
    const [sku, setSku] = useState('SKU-1');
    const [failed, setFailed] = useState(false);
    const navigate = useNavigate();
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setFailed(false);
        try {
            const order = await orderApi.createOrder({ items: [{ sku, quantity: 1, unitPriceCents: 500 }] });
            navigate(`/orders/${order.id}`);
        }
        catch {
            setFailed(true);
        }
    }
    return <form onSubmit={submit}><h1>Create order</h1><label>SKU<input value={sku} onChange={event => setSku(event.target.value)}/></label><button type="submit">Create</button>{failed && <p role="alert">Unable to create order</p>}</form>;
}
