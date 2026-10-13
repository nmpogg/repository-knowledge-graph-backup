export type OrderStatus = 'CREATED' | 'PAID' | 'PROCESSING' | 'SHIPPED' | 'CANCELLED';
export interface OrderItem { sku: string; quantity: number; unitPriceCents: number; }
export interface Order { id: string; status: OrderStatus; totalCents: number; items: OrderItem[]; }
export interface OrderRequest { items: OrderItem[]; }
export interface OrderUpdate { status: OrderStatus; }
