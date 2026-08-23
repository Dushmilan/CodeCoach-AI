import { HttpClient, HttpMethod, HttpRequestOptions } from "./http-client";
import { getAccessToken, setAccessToken, getCsrfToken } from "./auth-session";

declare const process: { env: { NEXT_PUBLIC_API_URL?: string } };

const DEFAULT_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MUTATING_METHODS: ReadonlySet<HttpMethod> = new Set<HttpMethod>([
  "POST",
  "PUT",
  "DELETE",
  "PATCH",
]);

export class FetchClient implements HttpClient {
  private baseUrl: string;
  private getToken: () => string | null;
  private refreshInFlight: Promise<boolean> | null = null;

  constructor(
    baseUrl: string = DEFAULT_BASE_URL,
    getToken?: () => string | null,
  ) {
    this.baseUrl = baseUrl;
    this.getToken = getToken ?? getAccessToken;
  }

  async get<T>(path: string, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>("GET", path, undefined, options);
  }

  async post<T>(
    path: string,
    body?: unknown,
    options?: HttpRequestOptions,
  ): Promise<T> {
    return this.request<T>("POST", path, body, options);
  }

  async put<T>(
    path: string,
    body?: unknown,
    options?: HttpRequestOptions,
  ): Promise<T> {
    return this.request<T>("PUT", path, body, options);
  }

  async delete<T>(path: string, options?: HttpRequestOptions): Promise<T> {
    return this.request<T>("DELETE", path, undefined, options);
  }

  private async refreshAccessToken(): Promise<boolean> {
    // SEC-2: refresh token lives in an httpOnly cookie; the browser sends it
    // automatically. The refresh endpoint is CSRF-exempt by design (see
    // backend auth.py), so no X-CSRF-Token header is required here.
    if (!this.refreshInFlight) {
      this.refreshInFlight = (async () => {
        try {
          const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
          });
          if (!response.ok) {
            setAccessToken(null);
            return false;
          }
          const data = (await response.json()) as {
            access_token: string;
          };
          setAccessToken(data.access_token);
          return true;
        } catch {
          setAccessToken(null);
          return false;
        } finally {
          this.refreshInFlight = null;
        }
      })();
    }

    return this.refreshInFlight;
  }

  private async request<T>(
    method: HttpMethod,
    path: string,
    body?: unknown,
    options?: HttpRequestOptions,
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutMs = options?.timeout ?? 10000;
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const signal = options?.signal
      ? anySignal([options.signal, controller.signal])
      : controller.signal;

    try {
      const token = this.getToken();
      const csrfToken = MUTATING_METHODS.has(method) ? getCsrfToken() : null;
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        ...options?.headers,
      };

      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
        cache: options?.cache,
        credentials: "include",
      });

      clearTimeout(timeoutId);

      if (
        !response.ok &&
        response.status === 401 &&
        path !== "/api/auth/refresh" &&
        !options?.skipAuthRefresh
      ) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          const retryHeaders = { ...options?.headers };
          delete retryHeaders.Authorization;
          return this.request<T>(method, path, body, {
            ...options,
            headers: retryHeaders,
            skipAuthRefresh: true,
          });
        }
      }

      if (!response.ok) {
        const errorBody = await response.text().catch(() => "");
        throw new HttpError(
          `Request failed: ${response.status} ${response.statusText}`,
          response.status,
          errorBody,
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
      const isAbort =
        error instanceof DOMException
          ? error.name === "AbortError"
          : error instanceof Error && error.name === "AbortError";
      if (isAbort) {
        throw new HttpError("Request timeout", 408);
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
    public readonly body?: string,
  ) {
    super(message);
    this.name = "HttpError";
  }
}

function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason);
      return controller.signal;
    }
    signal.addEventListener("abort", () => controller.abort(signal.reason), {
      once: true,
    });
  }
  return controller.signal;
}
