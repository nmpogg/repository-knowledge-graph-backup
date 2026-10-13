import { Worker, type ConnectionOptions, type Job, type Queue } from 'bullmq';
import type { ProcessOrderJobData, SendOrderEmailJobData } from '../domain/jobs.js';
import type { Order } from '../domain/order.js';
import { enqueueOrderEmail } from '../producers/emailProducer.js';
import type { OrderService } from '../services/orderService.js';
import { ORDER_QUEUE } from '../queues/names.js';

export interface OrderProcessorDependencies {
  orderService: Pick<OrderService, 'processOrder'>;
  emailQueue: Pick<Queue<SendOrderEmailJobData>, 'add'>;
}

export async function processOrderJob(
  job: Pick<Job<ProcessOrderJobData>, 'data'>,
  dependencies: OrderProcessorDependencies,
): Promise<Order> {
  const order = await dependencies.orderService.processOrder(job.data);
  await enqueueOrderEmail(dependencies.emailQueue, {
    orderId: order.id,
    customerId: order.customerId,
    template: 'order-processed',
  });
  return order;
}

export function createOrderWorker(
  connection: ConnectionOptions,
  concurrency: number,
  dependencies: OrderProcessorDependencies,
): Worker<ProcessOrderJobData, Order> {
  return new Worker<ProcessOrderJobData, Order>(
    ORDER_QUEUE,
    async (job) => processOrderJob(job, dependencies),
    { connection, concurrency },
  );
}
