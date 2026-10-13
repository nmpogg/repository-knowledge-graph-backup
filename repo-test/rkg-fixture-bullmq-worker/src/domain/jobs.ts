export interface ProcessOrderJobData {
  orderId: string;
  customerId: string;
  totalCents: number;
}

export interface SendOrderEmailJobData {
  orderId: string;
  customerId: string;
  template: 'order-processed';
}

export interface CleanupJobData {
  beforeDays: number;
}
