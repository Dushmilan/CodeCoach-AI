import { HttpClient, HttpMethod, HttpRequestOptions } from './http-client';

declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class FetchClient implements HttpClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>('GET', path, undefined, options);
  }

  async post<T>(path: string, body?: unknown, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>('POST', path, body, options);
  }

  async put<T>(path: string, body?: unknown, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>('PUT', path, body, options);
  }

  async delete<T>(path: string, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, undefined, options);
  }

  private async request<T>(
    method: HttpMethod,
    path: string,
    body?: unknown,
    options?: HttpRequestOptions
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutMs = options?.timeout ?? 10000;
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const signal = options?.signal
      ? anySignal([options.signal, controller.signal])
      : controller.signal;

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options?.headers,
      };

      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: body !== undefined ? headers : { ...headers, ...(options?.headers || {}) },
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
        cache: options?.cache,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorBody = await response.text().catch(() => '');
        throw new HttpError(
          `Request failed: ${response.status} ${response.statusText}`,
          response.status,
          errorBody
        );
      }

      if (this.isNoContent(response.status)) {
        return undefined as T;
      }

      return response.json() as Promise<T>;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof HttpError) {
        throw error;
      }
      if (error instanceof Error && error.name === 'AbortError') {
        throw new HttpError('Request timeout', 408);
      }
      throw error;
    }
  }

  private isNoContent(status: number): boolean {
    return status === 204 || status === 205;
  }
}

export class HttpError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: string
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      return controller.signal;
    }
    signal.addEventListener('abort', () => controller.abort(signal.reason), { once: true });
  }
  return controller.signal;
}
