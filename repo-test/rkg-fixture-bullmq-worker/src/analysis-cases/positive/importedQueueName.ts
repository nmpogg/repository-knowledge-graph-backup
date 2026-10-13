import { Queue, type ConnectionOptions } from 'bullmq';
import type { SendOrderEmailJobData } from '../../domain/jobs.js';
import { EMAIL_QUEUE as MAIL_CHANNEL } from '../../queues/names.js';

export function createAliasedEmailQueue(
  connection: ConnectionOptions,
): Queue<SendOrderEmailJobData> {
  return new Queue<SendOrderEmailJobData>(MAIL_CHANNEL, { connection });
}
