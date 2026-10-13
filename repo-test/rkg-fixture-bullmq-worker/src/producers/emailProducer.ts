import type { Queue } from 'bullmq';
import type { SendOrderEmailJobData } from '../domain/jobs.js';

export async function enqueueOrderEmail(
  queue: Pick<Queue<SendOrderEmailJobData>, 'add'>,
  message: SendOrderEmailJobData,
): Promise<void> {
  await queue.add('send-order-email', { ...message }, {
    attempts: 5,
    backoff: { type: 'fixed', delay: 2_000 },
    removeOnComplete: true,
  });
}
