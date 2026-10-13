import type { Queue, Worker } from 'bullmq';
import { describe, expect, it, vi } from 'vitest';
import type { RuntimeWiring } from '../src/index.js';
import { bootstrap } from '../src/index.js';
import type { CleanupJobData, ProcessOrderJobData, SendOrderEmailJobData } from '../src/domain/jobs.js';
import type { Order } from '../src/domain/order.js';

describe('bootstrap', () => {
  it('wires queues, workers, scheduler and shutdown using injected boundaries', async () => {
    const orderQueue = { add: vi.fn(), close: vi.fn().mockResolvedValue(undefined) } as unknown as Queue<ProcessOrderJobData>;
    const emailQueue = { add: vi.fn(), close: vi.fn().mockResolvedValue(undefined) } as unknown as Queue<SendOrderEmailJobData>;
    const cleanupQueue = { close: vi.fn().mockResolvedValue(undefined) } as unknown as Queue<CleanupJobData>;
    const orderWorker = { close: vi.fn().mockResolvedValue(undefined) } as unknown as Worker<ProcessOrderJobData, Order>;
    const emailWorker = { close: vi.fn().mockResolvedValue(undefined) } as unknown as Worker<SendOrderEmailJobData, void>;
    const wiring: RuntimeWiring = {
      createOrderQueue: vi.fn(() => orderQueue),
      createEmailQueue: vi.fn(() => emailQueue),
      createOrderWorker: vi.fn(() => orderWorker),
      createEmailWorker: vi.fn(() => emailWorker),
      createCleanupScheduler: vi.fn(async () => cleanupQueue),
    };

    const runtime = await bootstrap({
      REDIS_URL: 'redis://localhost:6379',
      ORDER_WORKER_CONCURRENCY: '3',
      EMAIL_FROM: 'worker@example.test',
    }, wiring);

    expect(wiring.createOrderQueue).toHaveBeenCalledOnce();
    expect(wiring.createOrderWorker).toHaveBeenCalledWith(
      expect.objectContaining({ host: 'localhost', port: 6379 }),
      3,
      expect.objectContaining({ orderService: expect.any(Object), emailQueue }),
    );
    expect(wiring.createCleanupScheduler).toHaveBeenCalledOnce();
    await runtime.close();
    expect(orderWorker.close).toHaveBeenCalledOnce();
    expect(emailQueue.close).toHaveBeenCalledOnce();
  });
});
