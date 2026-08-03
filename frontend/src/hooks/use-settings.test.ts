import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useSettings } from "./use-settings";

describe("useSettings", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns empty api key by default", () => {
    const { result } = renderHook(() => useSettings());
    expect(result.current.apiKey).toBe("");
  });

  it("does not read the api key from localStorage (not persisted)", () => {
    localStorage.setItem("nvidia_api_key", "sk-test-key");
    const { result } = renderHook(() => useSettings());
    expect(result.current.apiKey).toBe("");
  });

  it("sets api key in memory without persisting to localStorage", () => {
    const { result } = renderHook(() => useSettings());
    act(() => {
      result.current.setApiKey("sk-new-key");
    });
    expect(result.current.apiKey).toBe("sk-new-key");
    expect(localStorage.getItem("nvidia_api_key")).toBeNull();
  });
});
