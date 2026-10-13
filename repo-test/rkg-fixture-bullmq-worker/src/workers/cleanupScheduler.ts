import { Queue, type ConnectionOptions } from 'bullmq';
import type { CleanupJobData } from '../domain/jobs.js';
import { ORDER_QUEUE } from '../queues/names.js';

export async function createCleanupScheduler(
  connection: ConnectionOptions,
): Promise<Queue<CleanupJobData>> {
  const queue = new Queue<CleanupJobData>(ORDER_QUEUE, { connection });
  await queue.upsertJobScheduler(
    'daily-order-cleanup',
    { every: 86_400_000 },
    { name: 'cleanup-orders', data: { beforeDays: 30 } },
  );
  return queue;
}
