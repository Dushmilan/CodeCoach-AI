export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface HttpRequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeout?: number;
  cache?: RequestCache;
}

export interface HttpClient {
  get<T>(path: string, options?: HttpRequestOptions): Promise<T>;
  post<T>(path: string, body?: unknown, options?: HttpRequestOptions): Promise<T>;
  put<T>(path: string, body?: unknown, options?: HttpRequestOptions): Promise<T>;
  delete<T>(path: string, options?: HttpRequestOptions): Promise<T>;
}
