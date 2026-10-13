import { getEnvironment } from '@/config/environment';

export interface HttpClient {
  post<T>(path: string, body: unknown): Promise<T>;
  get<T>(path: string): Promise<T>;
  patch<T>(path: string, body: unknown): Promise<T>;
}

export class FetchHttpClient implements HttpClient {
  constructor(private readonly baseUrl: string) {}

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'GET' });
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
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
