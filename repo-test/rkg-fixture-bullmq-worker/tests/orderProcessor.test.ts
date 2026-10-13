import type { Job, Queue } from 'bullmq';
import { describe, expect, it, vi } from 'vitest';
import type { ProcessOrderJobData, SendOrderEmailJobData } from '../src/domain/jobs.js';
import { InMemoryOrderRepository } from '../src/repositories/inMemoryOrderRepository.js';
import { OrderService } from '../src/services/orderService.js';
import { processOrderJob } from '../src/workers/orderWorker.js';

describe('processOrderJob', () => {
  it('calls the service/repository and publishes the follow-up email job', async () => {
    const repository = new InMemoryOrderRepository();
    const orderService = new OrderService(repository);
    const add = vi.fn().mockResolvedValue(undefined);
    const emailQueue = { add } as unknown as Pick<Queue<SendOrderEmailJobData>, 'add'>;
    const data: ProcessOrderJobData = { orderId: 'ORD-2', customerId: 'CUS-2', totalCents: 2300 };

    const result = await processOrderJob(
      { data } as Pick<Job<ProcessOrderJobData>, 'data'>,
      { orderService, emailQueue },
    );

    expect(result.status).toBe('processed');
    await expect(repository.findById('ORD-2')).resolves.toEqual(result);
    expect(add).toHaveBeenCalledWith(
      'send-order-email',
      { orderId: 'ORD-2', customerId: 'CUS-2', template: 'order-processed' },
      expect.objectContaining({ attempts: 5 }),
    );
  });
});
