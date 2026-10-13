import { Queue, type ConnectionOptions } from 'bullmq';
import type { SendOrderEmailJobData } from '../domain/jobs.js';
// RKG_EXPECT: email-queue-producer
export function createEmailQueue(connection: ConnectionOptions): Queue<SendOrderEmailJobData> {
    return new Queue<SendOrderEmailJobData>('order-email', { connection });
}
