import { Worker, type ConnectionOptions, type Job } from 'bullmq';
import type { SendOrderEmailJobData } from '../domain/jobs.js';
import type { EmailService } from '../services/emailService.js';
import { EMAIL_QUEUE } from '../queues/names.js';
// RKG_EXPECT: email-process
export async function processEmailJob(job: Pick<Job<SendOrderEmailJobData>, 'data'>, emailService: Pick<EmailService, 'sendOrderEmail'>): Promise<void> {
    await emailService.sendOrderEmail(job.data);
}
// RKG_EXPECT: email-queue-consumer
export function createEmailWorker(connection: ConnectionOptions, emailService: Pick<EmailService, 'sendOrderEmail'>): Worker<SendOrderEmailJobData, void> {
    async function namedProcessor(job: Job<SendOrderEmailJobData>): Promise<void> {
        await processEmailJob(job, emailService);
    }
    return new Worker<SendOrderEmailJobData, void>(EMAIL_QUEUE, namedProcessor, {
        connection,
        concurrency: 2,
    });
}
