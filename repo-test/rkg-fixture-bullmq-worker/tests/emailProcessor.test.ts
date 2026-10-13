import type { Job } from 'bullmq';
import { describe, expect, it, vi } from 'vitest';
import type { SendOrderEmailJobData } from '../src/domain/jobs.js';
import { processEmailJob } from '../src/workers/emailWorker.js';

describe('processEmailJob', () => {
  it('delegates the minimal message to the email service', async () => {
    const sendOrderEmail = vi.fn().mockResolvedValue(undefined);
    const data: SendOrderEmailJobData = {
      orderId: 'ORD-3',
      customerId: 'CUS-3',
      template: 'order-processed',
    };

    await processEmailJob({ data } as Pick<Job<SendOrderEmailJobData>, 'data'>, { sendOrderEmail });

    expect(sendOrderEmail).toHaveBeenCalledWith(data);
  });
});
