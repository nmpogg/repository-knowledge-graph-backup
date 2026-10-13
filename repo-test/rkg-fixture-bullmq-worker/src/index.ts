import type { Queue, Worker } from 'bullmq';
import { parseEnvironment } from './config/environment.js';
import { createRedisConnection } from './config/redis.js';
import type { CleanupJobData, ProcessOrderJobData, SendOrderEmailJobData } from './domain/jobs.js';
import type { Order } from './domain/order.js';
import { OrderProducer } from './producers/orderProducer.js';
import { createEmailQueue } from './queues/emailQueue.js';
import { createOrderQueue } from './queues/orderQueue.js';
import { InMemoryOrderRepository } from './repositories/inMemoryOrderRepository.js';
import { EmailService } from './services/emailService.js';
import { OrderService } from './services/orderService.js';
import { createCleanupScheduler } from './workers/cleanupScheduler.js';
import { createEmailWorker } from './workers/emailWorker.js';
import { createOrderWorker, type OrderProcessorDependencies } from './workers/orderWorker.js';

export interface RuntimeWiring {
  createOrderQueue: typeof createOrderQueue;
  createEmailQueue: typeof createEmailQueue;
  createOrderWorker: typeof createOrderWorker;
  createEmailWorker: typeof createEmailWorker;
  createCleanupScheduler: typeof createCleanupScheduler;
}

export interface ApplicationRuntime {
  orderProducer: OrderProducer;
  orderQueue: Queue<ProcessOrderJobData>;
  emailQueue: Queue<SendOrderEmailJobData>;
  orderWorker: Worker<ProcessOrderJobData, Order>;
  emailWorker: Worker<SendOrderEmailJobData, void>;
  cleanupQueue: Queue<CleanupJobData>;
  close(): Promise<void>;
}

const defaultWiring: RuntimeWiring = {
  createOrderQueue,
  createEmailQueue,
  createOrderWorker,
  createEmailWorker,
  createCleanupScheduler,
};

export async function bootstrap(
  source: Record<string, string | undefined> = process.env,
  wiring: RuntimeWiring = defaultWiring,
): Promise<ApplicationRuntime> {
  const environment = parseEnvironment(source);
  const connection = createRedisConnection(environment.redisUrl);
  const orderQueue = wiring.createOrderQueue(connection);
  const emailQueue = wiring.createEmailQueue(connection);
  const orderService = new OrderService(new InMemoryOrderRepository());
  const emailService = new EmailService(environment.emailFrom);
  const processorDependencies: OrderProcessorDependencies = { orderService, emailQueue };
  const orderWorker = wiring.createOrderWorker(
    connection,
    environment.orderWorkerConcurrency,
    processorDependencies,
  );
  const emailWorker = wiring.createEmailWorker(connection, emailService);
  const cleanupQueue = await wiring.createCleanupScheduler(connection);

  return {
    orderProducer: new OrderProducer(orderQueue),
    orderQueue,
    emailQueue,
    orderWorker,
    emailWorker,
    cleanupQueue,
    async close() {
      await Promise.all([
        orderWorker.close(),
        emailWorker.close(),
        cleanupQueue.close(),
        orderQueue.close(),
        emailQueue.close(),
      ]);
    },
  };
}
