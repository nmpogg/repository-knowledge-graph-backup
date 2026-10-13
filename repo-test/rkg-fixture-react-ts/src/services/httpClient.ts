import { getEnvironment } from '@/config/environment';

export interface HttpClient {
  get<T>(path: string): Promise<T>;
  put<T>(path: string, body: unknown): Promise<T>;
}

export class FetchHttpClient implements HttpClient {
  constructor(private readonly baseUrl: string) {}

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'GET' });
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const response = await globalThis.fetch(`${this.baseUrl}${path}`, init);
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    return response.json() as Promise<T>;
  }
}

export const httpClient = new FetchHttpClient(getEnvironment().apiBaseUrl);
