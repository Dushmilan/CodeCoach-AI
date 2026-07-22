import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAuthGuard } from "./AuthGuard";

const mockPush = vi.fn();
const mockPathname = "/test-page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockPathname,
}));

describe("useAuthGuard", () => {
  beforeEach(() => {
    mockPush.mockReset();
  });

  it("returns isLoading and isAuthenticated from auth context", () => {
    vi.mock("@/providers", () => ({
      useAuth: () => ({ isAuthenticated: true, isLoading: false }),
    }));

    const { result, rerender } = renderHook(() => useAuthGuard());
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });

  it("allows action when authenticated", () => {
    vi.mock("@/providers", () => ({
      useAuth: () => ({ isAuthenticated: true, isLoading: false }),
    }));

    const { result, rerender } = renderHook(() => useAuthGuard());
    const allowed = result.current.requireAuth("run");
    expect(allowed).toBe(true);
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("redirects to login when not authenticated", () => {
    vi.mock("@/providers", () => ({
      useAuth: () => ({ isAuthenticated: false, isLoading: false }),
    }));

    const { result, rerender } = renderHook(() => useAuthGuard());
    const allowed = result.current.requireAuth("coach");
    expect(allowed).toBe(false);
    expect(mockPush).toHaveBeenCalledWith(
      "/login?redirect=%2Ftest-page&action=coach",
    );
  });

  it("returns false when still loading", () => {
    vi.mock("@/providers", () => ({
      useAuth: () => ({ isAuthenticated: false, isLoading: true }),
    }));

    const { result, rerender } = renderHook(() => useAuthGuard());
    const allowed = result.current.requireAuth("run");
    expect(allowed).toBe(false);
    expect(mockPush).not.toHaveBeenCalled();
  });
});
