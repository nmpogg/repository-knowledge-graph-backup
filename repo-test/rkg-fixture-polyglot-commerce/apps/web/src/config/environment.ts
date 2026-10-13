export interface Environment {
    apiBaseUrl: string;
}
type EnvironmentSource = Record<string, string | boolean | undefined>;
export function parseEnvironment(source: EnvironmentSource): Environment {
    const raw = source.VITE_API_BASE_URL;
    if (raw !== undefined && typeof raw !== 'string')
        throw new Error('Invalid web configuration');
    const apiBaseUrl = (raw ?? '').trim().replace(/\/$/, '');
    if (apiBaseUrl) {
        let url: URL;
        try {
            url = new URL(apiBaseUrl);
        }
        catch {
            throw new Error('Invalid web configuration');
        }
        if (!['http:', 'https:'].includes(url.protocol))
            throw new Error('Invalid web configuration');
    }
    return { apiBaseUrl };
}
export function getEnvironment(): Environment { return parseEnvironment(import.meta.env); }
