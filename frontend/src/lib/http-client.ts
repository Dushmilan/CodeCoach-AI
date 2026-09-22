export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

/** Receives one text chunk from a streaming (SSE) response. */
export type StreamChunkHandler = (chunk: string) => void;

export interface HttpRequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeout?: number;
  cache?: RequestCache;
  /** Internal: prevents infinite retry loops after a token refresh (401). */
  skipAuthRefresh?: boolean;
}

export interface HttpClient {
  get<T>(path: string, options?: HttpRequestOptions): Promise<T>;
  post<T>(
    path: string,
    body?: unknown,
    options?: HttpRequestOptions,
  ): Promise<T>;
  put<T>(
    path: string,
    body?: unknown,
    options?: HttpRequestOptions,
  ): Promise<T>;
  delete<T>(path: string, options?: HttpRequestOptions): Promise<T>;
  /** POST + Server-Sent Events. Optional so test doubles can omit it. */
  stream?(
    path: string,
    body: unknown,
    onChunk: StreamChunkHandler,
    options?: HttpRequestOptions,
  ): Promise<void>;
}
