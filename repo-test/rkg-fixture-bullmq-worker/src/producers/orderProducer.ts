import type { Queue } from 'bullmq';
import type { ProcessOrderJobData } from '../domain/jobs.js';

export class OrderProducer {
  constructor(private readonly queue: Pick<Queue<ProcessOrderJobData>, 'add'>) {}

  async enqueue(request: ProcessOrderJobData): Promise<void> {
    const payload = { ...request };
    await this.queue.add('process-order', payload, {
      attempts: 3,
      backoff: { type: 'exponential', delay: 1_000 },
      delay: 250,
      removeOnComplete: true,
    });
  }
}
