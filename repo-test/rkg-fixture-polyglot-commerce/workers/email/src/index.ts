import { parseEnvironment } from './config/environment.js';
import { createRedisConnection } from './config/redis.js';
import { createEmailQueue } from './queues/emailQueue.js';
import { createEmailWorker } from './workers/emailWorker.js';
import { EmailService } from './services/emailService.js';
export async function bootstrap(source: Record<string, string | undefined> = process.env) {
    const env = parseEnvironment(source);
    const connection = createRedisConnection(env.redisUrl);
    const queue = createEmailQueue(connection);
    const worker = createEmailWorker(connection, new EmailService(env.emailFrom));
    return { queue, worker, async close() { await worker.close(); await queue.close(); } };
}
