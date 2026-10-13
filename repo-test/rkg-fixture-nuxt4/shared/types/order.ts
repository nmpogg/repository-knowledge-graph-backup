export type OrderStatus = 'pending' | 'processing' | 'shipped' | 'cancelled'

export interface Order {
  id: string
  customerName: string
  totalCents: number
  status: OrderStatus
  updatedAt: string
}
