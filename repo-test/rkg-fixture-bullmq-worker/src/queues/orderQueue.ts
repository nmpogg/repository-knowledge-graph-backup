import { Queue, type ConnectionOptions } from 'bullmq';
import type { ProcessOrderJobData } from '../domain/jobs.js';
import { ORDER_QUEUE } from './names.js';

export function createOrderQueue(connection: ConnectionOptions): Queue<ProcessOrderJobData> {
  return new Queue<ProcessOrderJobData>(ORDER_QUEUE, { connection });
}
