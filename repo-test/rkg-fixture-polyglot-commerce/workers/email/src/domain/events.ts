export const ORDERS_TOPIC = 'orders.events';
export interface OrderEvent {
    type: 'order.updated';
    order_id: string;
    status: string;
    occurred_at: string;
}
export function validateOrderEvent(event: OrderEvent): void {
    if (!['CREATED', 'PAID', 'PROCESSING', 'SHIPPED', 'CANCELLED'].includes(event.status) || event.type !== 'order.updated' || !event.order_id || !event.status || Number.isNaN(Date.parse(event.occurred_at)))
        throw new Error('Invalid order event');
}
