export interface Environment {
    redisUrl: string;
    emailFrom: string;
}
export function parseEnvironment(source: Record<string, string | undefined>): Environment {
    const redisUrl = source.REDIS_URL ?? 'redis://localhost:6379';
    const emailFrom = source.EMAIL_FROM ?? 'orders@example.test';
    let url: URL;
    try {
        url = new URL(redisUrl);
    }
    catch {
        throw new Error('Invalid email worker configuration');
    }
    if (!['redis:', 'rediss:'].includes(url.protocol) || !emailFrom.includes('@'))
        throw new Error('Invalid email worker configuration');
    return { redisUrl, emailFrom };
}
