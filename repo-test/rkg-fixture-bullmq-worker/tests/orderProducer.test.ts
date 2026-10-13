import type { Queue } from 'bullmq';
import { describe, expect, it, vi } from 'vitest';
import type { ProcessOrderJobData } from '../src/domain/jobs.js';
import { OrderProducer } from '../src/producers/orderProducer.js';

describe('OrderProducer', () => {
  it('enqueues process-order with static retry/delay options without mutating the request', async () => {
    const add = vi.fn().mockResolvedValue(undefined);
    const queue = { add } as unknown as Pick<Queue<ProcessOrderJobData>, 'add'>;
    const producer = new OrderProducer(queue);
    const request: ProcessOrderJobData = { orderId: 'ORD-1', customerId: 'CUS-1', totalCents: 1250 };
    const snapshot = { ...request };

    await producer.enqueue(request);

    expect(request).toEqual(snapshot);
    expect(add).toHaveBeenCalledWith(
      'process-order',
      snapshot,
      expect.objectContaining({ attempts: 3, delay: 250 }),
    );
    expect(add.mock.calls[0]?.[1]).not.toBe(request);
  });
});
