import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { UsageProvider, useUsage } from "./usage.context";
import { usageService } from "./usage.service";

vi.mock("./usage.service", () => ({
  usageService: { getUsage: vi.fn() },
}));

const mockGetUsage = vi.mocked(usageService.getUsage);

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <UsageProvider>{children}</UsageProvider>
);

const sampleUsage = {
  plan: "free",
  daily_limit: 20,
  daily_used: 6,
  daily_remaining: 14,
  reset_at: "2026-08-07T00:00:00+00:00",
};

describe("useUsage", () => {
  beforeEach(() => {
    mockGetUsage.mockReset();
  });

  it("provides safe defaults outside a provider", () => {
    const { result } = renderHook(() => useUsage());
    expect(result.current.usage).toBeNull();
    expect(result.current.limitReached).toBe(false);
    expect(result.current.upgradeOpen).toBe(false);
  });

  it("starts with null usage inside a provider", async () => {
    mockGetUsage.mockRejectedValue(new Error("not logged in"));
    const { result } = renderHook(() => useUsage(), { wrapper });
    await waitFor(() => expect(result.current.usage).toBeNull());
  });

  it("refreshUsage populates usage", async () => {
    mockGetUsage.mockResolvedValue(sampleUsage);
    const { result } = renderHook(() => useUsage(), { wrapper });
    await waitFor(() => expect(result.current.usage).toEqual(sampleUsage));
  });

  it("markLimitReached sets the flag and clearLimitReached resets it", () => {
    const { result } = renderHook(() => useUsage(), { wrapper });
    act(() => result.current.markLimitReached());
    expect(result.current.limitReached).toBe(true);
    act(() => result.current.clearLimitReached());
    expect(result.current.limitReached).toBe(false);
  });

  it("openUpgrade/closeUpgrade toggle the modal flag", () => {
    const { result } = renderHook(() => useUsage(), { wrapper });
    act(() => result.current.openUpgrade());
    expect(result.current.upgradeOpen).toBe(true);
    act(() => result.current.closeUpgrade());
    expect(result.current.upgradeOpen).toBe(false);
  });

  it("refreshUsage keeps last usage on failure", async () => {
    mockGetUsage
      .mockResolvedValueOnce(sampleUsage) // mount effect
      .mockRejectedValueOnce(new Error("network")); // explicit call
    const { result } = renderHook(() => useUsage(), { wrapper });
    await waitFor(() => expect(result.current.usage).toEqual(sampleUsage));
    await act(async () => {
      await result.current.refreshUsage();
    });
    expect(result.current.usage).toEqual(sampleUsage);
  });
});
