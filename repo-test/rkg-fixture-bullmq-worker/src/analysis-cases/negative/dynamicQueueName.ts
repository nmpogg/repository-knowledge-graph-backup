import { Queue, type ConnectionOptions } from 'bullmq';

// Expected: diagnostic only; do not guess a MessageChannel for this runtime queue name.
export function createDynamicQueue(queueName: string, connection: ConnectionOptions): Queue {
  return new Queue(queueName, { connection });
}
