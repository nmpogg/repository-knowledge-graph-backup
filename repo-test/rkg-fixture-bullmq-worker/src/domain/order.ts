export type OrderStatus = 'processed';

export interface Order {
  id: string;
  customerId: string;
  totalCents: number;
  status: OrderStatus;
}
