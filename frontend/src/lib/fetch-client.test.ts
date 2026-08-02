import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { FetchClient, HttpError } from "./fetch-client";

function createMockResponse(overrides: Partial<Response> = {}): Response {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    json: vi.fn().mockResolvedValue({ data: "ok" }),
    text: vi.fn().mockResolvedValue(""),
    headers: new Headers(),
    redirected: false,
    type: "basic",
    url: "",
    clone: vi.fn(),
    body: null,
    bodyUsed: false,
    blob: vi.fn(),
    arrayBuffer: vi.fn(),
    formData: vi.fn(),
    ...overrides,
  } as unknown as Response;
}

describe("FetchClient", () => {
  let client: FetchClient;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    globalThis.fetch = fetchSpy as unknown as typeof globalThis.fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("constructor", () => {
    it("uses default base URL when none provided", () => {
      client = new FetchClient();
      fetchSpy.mockResolvedValue(createMockResponse());
      client.get("/api/test");
      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/test",
        expect.anything(),
      );
    });

    it("uses custom base URL when provided", () => {
      client = new FetchClient("http://custom:3000");
      fetchSpy.mockResolvedValue(createMockResponse());
      client.get("/api/test");
      expect(fetchSpy).toHaveBeenCalledWith(
        "http://custom:3000/api/test",
        expect.anything(),
      );
    });
  });

  describe("GET", () => {
    it("sends GET request and returns JSON", async () => {
      const mockResponse = createMockResponse({
        json: vi.fn().mockResolvedValue({ items: [1, 2] }),
      });
      fetchSpy.mockResolvedValue(mockResponse);
      client = new FetchClient();

      const result = await client.get<{ items: number[] }>("/api/items");

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/items",
        expect.objectContaining({ method: "GET" }),
      );
      expect(result).toEqual({ items: [1, 2] });
    });

    it("passes custom headers", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.get("/api/items", {
        headers: { Authorization: "Bearer token" },
      });

      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      const headers = callArgs.headers as Record<string, string>;
      expect(headers["Authorization"]).toBe("Bearer token");
    });
  });

  describe("POST", () => {
    it("sends POST request with JSON body", async () => {
      fetchSpy.mockResolvedValue(
        createMockResponse({ json: vi.fn().mockResolvedValue({ id: 1 }) }),
      );
      client = new FetchClient();

      const body = { name: "test" };
      const result = await client.post<{ id: number }>("/api/items", body);

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/items",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(body),
        }),
      );

      const callHeaders = (fetchSpy.mock.calls[0][1] as RequestInit)
        .headers as Record<string, string>;
      expect(callHeaders["Content-Type"]).toBe("application/json");
      expect(result).toEqual({ id: 1 });
    });

    it("sends POST without body", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.post("/api/empty");

      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      expect(callArgs.method).toBe("POST");
      expect(callArgs.body).toBeUndefined();
    });

    it("includes Content-Type when body is present", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.post("/api/create", { name: "test" });
      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      const headers = callArgs.headers as Record<string, string>;

      expect(headers["Content-Type"]).toBe("application/json");
      expect(callArgs.body).toBe(JSON.stringify({ name: "test" }));
    });

    it("always sends Content-Type header even without body", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.post("/api/empty");
      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      const headers = callArgs.headers as Record<string, string>;

      expect(headers["Content-Type"]).toBe("application/json");
      expect(callArgs.body).toBeUndefined();
    });
  });

  describe("PUT", () => {
    it("sends PUT request with JSON body", async () => {
      fetchSpy.mockResolvedValue(
        createMockResponse({
          json: vi.fn().mockResolvedValue({ updated: true }),
        }),
      );
      client = new FetchClient();

      const result = await client.put("/api/items/1", { name: "updated" });

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/items/1",
        expect.objectContaining({ method: "PUT" }),
      );
      expect(result).toEqual({ updated: true });
    });
  });

  describe("DELETE", () => {
    it("sends DELETE request", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.delete("/api/items/1");

      expect(fetchSpy).toHaveBeenCalledWith(
        "http://localhost:8000/api/items/1",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  describe("error handling", () => {
    it("throws HttpError on non-ok response", async () => {
      fetchSpy.mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 404,
          statusText: "Not Found",
          text: vi.fn().mockResolvedValue('{"error":"missing"}'),
        }),
      );
      client = new FetchClient();

      await expect(client.get("/api/missing")).rejects.toThrow(HttpError);
      await expect(client.get("/api/missing")).rejects.toMatchObject({
        status: 404,
        body: '{"error":"missing"}',
      });
    });

    it("throws HttpError on server error", async () => {
      fetchSpy.mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
          text: vi.fn().mockResolvedValue("Server crashed"),
        }),
      );
      client = new FetchClient();

      await expect(client.get("/api/error")).rejects.toMatchObject({
        status: 500,
      });
    });

    it("throws HttpError 408 on abort/timeout", async () => {
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      fetchSpy.mockRejectedValue(abortError);
      client = new FetchClient();

      await expect(client.get("/api/slow")).rejects.toMatchObject({
        status: 408,
      });
    });

    it("re-throws HttpError as-is", async () => {
      fetchSpy.mockRejectedValue(
        new HttpError("Custom error", 403, "forbidden"),
      );
      client = new FetchClient();

      await expect(client.get("/api/forbidden")).rejects.toMatchObject({
        status: 403,
        message: "Custom error",
      });
    });

    it("handles text() failure on error response gracefully", async () => {
      const badResponse = createMockResponse({
        ok: false,
        status: 400,
        text: vi.fn().mockRejectedValue(new Error("stream error")),
      });
      fetchSpy.mockResolvedValue(badResponse);
      client = new FetchClient();

      const err = await client.get("/api/bad").catch((e: unknown) => e);
      expect((err as HttpError).status).toBe(400);
      expect((err as HttpError).body).toBe("");
    });
  });

  describe("no-content responses", () => {
    it.each([204, 205])("returns undefined for status %i", async (status) => {
      fetchSpy.mockResolvedValue(createMockResponse({ status, ok: true }));
      client = new FetchClient();

      const result = await client.get("/api/empty");
      expect(result).toBeUndefined();
    });
  });

  describe("request options", () => {
    it("passes cache option to fetch", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      await client.get("/api/data", { cache: "no-store" });

      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      expect(callArgs.cache).toBe("no-store");
    });

    it("passes external abort signal to fetch", async () => {
      fetchSpy.mockResolvedValue(createMockResponse());
      client = new FetchClient();

      const controller = new AbortController();
      await client.get("/api/data", { signal: controller.signal });

      const callArgs = fetchSpy.mock.calls[0][1] as RequestInit;
      expect(callArgs.signal).toBeDefined();
    });
  });

  describe("refresh-on-401", () => {
    let storage: Map<string, string>;

    beforeEach(() => {
      storage = new Map();
      vi.stubGlobal("localStorage", {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
        clear: () => storage.clear(),
      });
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("refreshes token and retries original request on 401", async () => {
      storage.set("auth_token", JSON.stringify("expired_jwt"));
      storage.set("auth_refresh_token", JSON.stringify("valid_refresh"));
      client = new FetchClient();

      fetchSpy
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: "Unauthorized",
            text: vi.fn().mockResolvedValue("expired"),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            json: vi.fn().mockResolvedValue({
              access_token: "new_jwt",
              refresh_token: "rotated_refresh",
              token_type: "bearer",
              expires_in: 1800,
              user: { id: "1", username: "u" },
            }),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            json: vi.fn().mockResolvedValue({ protected: true }),
          }),
        );

      const result = await client.get("/api/protected");

      expect(result).toEqual({ protected: true });
      expect(fetchSpy).toHaveBeenNthCalledWith(
        2,
        "http://localhost:8000/api/auth/refresh",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ refresh_token: "valid_refresh" }),
        }),
      );
      expect(storage.get("auth_token")).toBe(JSON.stringify("new_jwt"));
      expect(storage.get("auth_refresh_token")).toBe(
        JSON.stringify("rotated_refresh"),
      );
      const retryCall = fetchSpy.mock.calls[2][1] as RequestInit;
      const retryHeaders = retryCall.headers as Record<string, string>;
      expect(retryHeaders["Authorization"]).toBe("Bearer new_jwt");
    });

    it("does not retry when no refresh token is stored", async () => {
      storage.set("auth_token", JSON.stringify("expired_jwt"));
      client = new FetchClient();

      fetchSpy.mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 401,
          statusText: "Unauthorized",
          text: vi.fn().mockResolvedValue("expired"),
        }),
      );

      await expect(client.get("/api/protected")).rejects.toMatchObject({
        status: 401,
      });
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    it("clears tokens and does not retry when refresh fails", async () => {
      storage.set("auth_token", JSON.stringify("expired_jwt"));
      storage.set("auth_refresh_token", JSON.stringify("bad_refresh"));
      client = new FetchClient();

      fetchSpy
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: "Unauthorized",
            text: vi.fn().mockResolvedValue("expired"),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: "Unauthorized",
            text: vi.fn().mockResolvedValue("invalid refresh"),
          }),
        );

      await expect(client.get("/api/protected")).rejects.toMatchObject({
        status: 401,
      });
      expect(fetchSpy).toHaveBeenCalledTimes(2);
      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(localStorage.getItem("auth_refresh_token")).toBeNull();
    });

    it("single-flights concurrent refresh requests", async () => {
      storage.set("auth_token", JSON.stringify("expired_jwt"));
      storage.set("auth_refresh_token", JSON.stringify("valid_refresh"));
      client = new FetchClient();

      fetchSpy
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: "Unauthorized",
            text: vi.fn().mockResolvedValue("expired"),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: "Unauthorized",
            text: vi.fn().mockResolvedValue("expired"),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            json: vi.fn().mockResolvedValue({
              access_token: "new_jwt",
              token_type: "bearer",
              expires_in: 1800,
              user: { id: "1", username: "u" },
            }),
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({ json: vi.fn().mockResolvedValue({ a: 1 }) }),
        )
        .mockResolvedValueOnce(
          createMockResponse({ json: vi.fn().mockResolvedValue({ b: 2 }) }),
        );

      const [resultA, resultB] = await Promise.all([
        client.get("/api/a"),
        client.get("/api/b"),
      ]);

      expect(resultA).toEqual({ a: 1 });
      expect(resultB).toEqual({ b: 2 });
      const refreshCalls = fetchSpy.mock.calls.filter(
        ([url]) => url === "http://localhost:8000/api/auth/refresh",
      );
      expect(refreshCalls).toHaveLength(1);
    });
  });
});
