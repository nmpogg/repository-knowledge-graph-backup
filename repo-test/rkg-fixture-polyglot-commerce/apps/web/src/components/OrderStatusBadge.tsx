import type { OrderStatus } from '@/domain/order';

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status status--${status}`}>{status}</span>;
}
