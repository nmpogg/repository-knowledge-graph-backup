export interface WorkerEnvironment {
  redisUrl: string;
  orderWorkerConcurrency: number;
  emailFrom: string;
}

type EnvironmentSource = Record<string, string | undefined>;

export function parseEnvironment(source: EnvironmentSource): WorkerEnvironment {
  const redisUrl = source.REDIS_URL?.trim();
  const emailFrom = source.EMAIL_FROM?.trim();
  const concurrency = Number(source.ORDER_WORKER_CONCURRENCY);

  if (!redisUrl) throw new Error('REDIS_URL is required');
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 100) {
    throw new Error('ORDER_WORKER_CONCURRENCY must be an integer from 1 to 100');
  }
  if (!emailFrom) throw new Error('EMAIL_FROM is required');

  return { redisUrl, orderWorkerConcurrency: concurrency, emailFrom };
}
