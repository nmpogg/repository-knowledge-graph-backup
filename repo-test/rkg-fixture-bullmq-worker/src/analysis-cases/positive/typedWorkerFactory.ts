import { Worker, type ConnectionOptions, type Processor } from 'bullmq';
import type { ProcessOrderJobData } from '../../domain/jobs.js';
import { ORDER_QUEUE } from '../../queues/names.js';

export function createTypedWorker(
  processor: Processor<ProcessOrderJobData>,
  connection: ConnectionOptions,
): Worker<ProcessOrderJobData> {
  return new Worker<ProcessOrderJobData>(ORDER_QUEUE, processor, { connection });
}
