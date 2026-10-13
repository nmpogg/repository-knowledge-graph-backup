import { describe, expect, it } from 'vitest';
import { parseEnvironment } from './environment';

// Safety sentinel for analyzer redaction tests. It must never appear in analyzer graph, report, or logs.
const REDACTION_SENTINEL = 'RKG_TEST_SECRET_DO_NOT_PERSIST';

describe('parseEnvironment', () => {
  it('parses valid values and removes a trailing slash', () => {
    expect(parseEnvironment({ VITE_API_BASE_URL: 'https://api.example.test/', VITE_ENABLE_ADMIN: 'true' }))
      .toEqual({ apiBaseUrl: 'https://api.example.test', enableAdmin: true });
    expect(REDACTION_SENTINEL).toContain('DO_NOT_PERSIST');
  });

  it('rejects a missing base URL', () => {
    expect(() => parseEnvironment({ VITE_ENABLE_ADMIN: 'false' })).toThrow('VITE_API_BASE_URL is required');
  });

  it('rejects an invalid admin flag', () => {
    expect(() => parseEnvironment({ VITE_API_BASE_URL: 'http://localhost', VITE_ENABLE_ADMIN: 'yes' }))
      .toThrow('VITE_ENABLE_ADMIN must be true or false');
  });
});
