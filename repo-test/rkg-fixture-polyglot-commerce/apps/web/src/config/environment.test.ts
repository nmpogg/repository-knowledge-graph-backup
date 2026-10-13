import { describe, expect, it } from 'vitest';
import { parseEnvironment } from './environment';
const REDACTION_SENTINEL = 'RKG_TEST_SECRET_DO_NOT_PERSIST';
describe('safe same-origin defaults', () => {
    it('parses an explicit HTTP origin and trims its trailing slash', () => {
        expect(parseEnvironment({ VITE_API_BASE_URL: 'https://api.example.test/' })).toEqual({ apiBaseUrl: 'https://api.example.test' });
    });
    it('uses relative /api requests without a local env file', () => {
        expect(parseEnvironment({})).toEqual({ apiBaseUrl: '' });
    });
    it('rejects non-HTTP origins without echoing the input', () => {
        expect(() => parseEnvironment({ VITE_API_BASE_URL: 'javascript:' + REDACTION_SENTINEL })).toThrow('Invalid web configuration');
    });
});
