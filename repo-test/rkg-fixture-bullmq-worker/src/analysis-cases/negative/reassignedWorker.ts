import { Worker, type ConnectionOptions, type Processor } from 'bullmq';
import type { ProcessOrderJobData } from '../../domain/jobs.js';
import { ORDER_QUEUE } from '../../queues/names.js';

interface CloseableWorker { close(): Promise<void> }
type WorkerConstructor = new (...arguments_: unknown[]) => CloseableWorker;

class LocalWorker implements CloseableWorker {
  async close(): Promise<void> { await Promise.resolve(); }
}

// Expected: no consume edge because the constructor receiver can be BullMQ Worker or a local class.
export function createReassignedWorker(
  useLocal: boolean,
  processor: Processor<ProcessOrderJobData>,
  connection: ConnectionOptions,
): CloseableWorker {
  let WorkerReceiver = Worker as unknown as WorkerConstructor;
  if (useLocal) WorkerReceiver = LocalWorker;
  return new WorkerReceiver(ORDER_QUEUE, processor, { connection });
}
