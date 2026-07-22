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

  it("reads existing api key from localStorage", () => {
    localStorage.setItem("nvidia_api_key", "sk-test-key");
    const { result } = renderHook(() => useSettings());
    expect(result.current.apiKey).toBe("sk-test-key");
  });

  it("sets api key and persists to localStorage", () => {
    const { result } = renderHook(() => useSettings());
    act(() => {
      result.current.setApiKey("sk-new-key");
    });
    expect(result.current.apiKey).toBe("sk-new-key");
    expect(localStorage.getItem("nvidia_api_key")).toBe("sk-new-key");
  });

  it("removes api key from localStorage when set to empty", () => {
    localStorage.setItem("nvidia_api_key", "sk-existing");
    const { result } = renderHook(() => useSettings());
    act(() => {
      result.current.setApiKey("");
    });
    expect(result.current.apiKey).toBe("");
    expect(localStorage.getItem("nvidia_api_key")).toBeNull();
  });
});
