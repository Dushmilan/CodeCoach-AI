import { describe, it, expect, vi, beforeEach } from "vitest";
import { FetchClient, HttpError } from "./fetch-client";
import { setAccessToken, clearTokens } from "./token-store";

function createMockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  });
}

describe("FetchClient", () => {
  let client: FetchClient;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
    clearTokens();
  });

  it("makes GET request", async () => {
    const mockData = { id: "1", name: "test" };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockData),
    } as Response);

    client = new FetchClient("http://test");
    const result = await client.get("/api/test");
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      "http://test/api/test",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("makes POST request with body", async () => {
    const mockData = { id: "1" };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(mockData),
    } as Response);

    client = new FetchClient("http://test");
    const result = await client.post("/api/test", { name: "new" });
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      "http://test/api/test",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "new" }),
      }),
    );
  });

  it("makes PUT request", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ updated: true }),
    } as Response);

    client = new FetchClient("http://test");
    const result = await client.put("/api/test/1", { name: "updated" });
    expect(result).toEqual({ updated: true });
  });

  it("makes DELETE request", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.resolve(undefined),
    } as Response);

    client = new FetchClient("http://test");
    const result = await client.delete("/api/test/1");
    expect(result).toBeUndefined();
  });

  it("throws HttpError on non-ok response", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve("Not found"),
    } as Response);

    client = new FetchClient("http://test");
    await expect(client.get("/api/test/999")).rejects.toThrow(HttpError);
  });

  it("includes auth token from token store", async () => {
    setAccessToken("test-token");
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    } as Response);

    client = new FetchClient("http://test");
    await client.get("/api/auth/me");
    const callArgs = vi.mocked(fetch).mock.calls[0][1] as RequestInit;
    const headers = callArgs.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-token");
  });

  it("times out after specified duration", async () => {
    vi.mocked(fetch).mockImplementation(
      () =>
        new Promise((_, reject) => {
          setTimeout(
            () => reject(new DOMException("Timeout", "AbortError")),
            100,
          );
        }),
    );

    client = new FetchClient("http://test");
    await expect(client.get("/api/test", { timeout: 10 })).rejects.toThrow(
      HttpError,
    );
  });
});
