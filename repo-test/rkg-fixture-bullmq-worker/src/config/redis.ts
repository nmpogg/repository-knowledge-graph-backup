import type { ConnectionOptions } from 'bullmq';

export function createRedisConnection(redisUrl: string): ConnectionOptions {
  const parsed = new URL(redisUrl);
  if (parsed.protocol !== 'redis:' && parsed.protocol !== 'rediss:') {
    throw new Error('REDIS_URL must use redis or rediss');
  }

  return {
    host: parsed.hostname,
    port: parsed.port ? Number(parsed.port) : 6379,
    username: parsed.username || undefined,
    password: parsed.password || undefined,
    ...(parsed.protocol === 'rediss:' ? { tls: {} } : {}),
  } as ConnectionOptions;
}
