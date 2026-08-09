import { describe, it, expect, vi } from "vitest";
import { UsageService } from "./usage.service";
import { HttpClient } from "@/lib/http-client";

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

describe("UsageService", () => {
  it("fetches /api/usage", async () => {
    const http = createMockHttp();
    const usage = {
      plan: "free",
      daily_limit: 20,
      daily_used: 5,
      daily_remaining: 15,
      reset_at: "2026-08-07T00:00:00+00:00",
    };
    vi.mocked(http.get).mockResolvedValue(usage);

    const service = new UsageService(http);
    await expect(service.getUsage()).resolves.toEqual(usage);
    expect(http.get).toHaveBeenCalledWith("/api/usage");
  });

  it("rethrows backend errors", async () => {
    const http = createMockHttp();
    vi.mocked(http.get).mockRejectedValue(new Error("Request failed: 429"));

    const service = new UsageService(http);
    await expect(service.getUsage()).rejects.toThrow("Request failed: 429");
  });
});
