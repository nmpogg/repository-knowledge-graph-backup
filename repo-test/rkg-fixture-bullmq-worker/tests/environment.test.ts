import { describe, expect, it } from 'vitest';
import { parseEnvironment } from '../src/config/environment.js';

// Redaction fixture only: this value must never be persisted in analyzer graphs, reports, or logs.
const REDACTION_SENTINEL = 'RKG_TEST_SECRET_DO_NOT_PERSIST';

describe('parseEnvironment', () => {
  it('parses a valid environment', () => {
    expect(parseEnvironment({
      REDIS_URL: 'redis://localhost:6379',
      ORDER_WORKER_CONCURRENCY: '7',
      EMAIL_FROM: 'worker@example.test',
    })).toEqual({
      redisUrl: 'redis://localhost:6379',
      orderWorkerConcurrency: 7,
      emailFrom: 'worker@example.test',
    });
    expect(REDACTION_SENTINEL).toContain('DO_NOT_PERSIST');
  });

  it.each(['0', '1.5', '101', 'not-a-number'])(
    'rejects invalid concurrency %s',
    (value) => {
      expect(() => parseEnvironment({
        REDIS_URL: 'redis://localhost:6379',
        ORDER_WORKER_CONCURRENCY: value,
        EMAIL_FROM: 'worker@example.test',
      })).toThrow('ORDER_WORKER_CONCURRENCY');
    },
  );

  it('rejects missing required keys', () => {
    expect(() => parseEnvironment({ ORDER_WORKER_CONCURRENCY: '2' })).toThrow('REDIS_URL');
  });
});
