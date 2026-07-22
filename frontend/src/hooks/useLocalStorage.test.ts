import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { useLocalStorage } from "./useLocalStorage";

describe("useLocalStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns initial value when key is not set", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", "default"));
    expect(result.current[0]).toBe("default");
  });

  it("reads existing value from localStorage", () => {
    localStorage.setItem("test-key", JSON.stringify("stored"));
    const { result } = renderHook(() => useLocalStorage("test-key", "default"));
    expect(result.current[0]).toBe("stored");
  });

  it("sets value and persists to localStorage", () => {
    const { result } = renderHook(() => useLocalStorage("test-key", "default"));
    act(() => {
      result.current[1]("updated");
    });
    expect(result.current[0]).toBe("updated");
    expect(JSON.parse(localStorage.getItem("test-key")!)).toBe("updated");
  });

  it("supports functional updater", () => {
    const { result } = renderHook(() => useLocalStorage<number>("counter", 0));
    act(() => {
      result.current[1]((prev) => prev + 1);
    });
    expect(result.current[0]).toBe(1);
  });

  it("removes value from localStorage", () => {
    localStorage.setItem("test-key", JSON.stringify("stored"));
    const { result } = renderHook(() => useLocalStorage("test-key", "default"));
    act(() => {
      result.current[2]();
    });
    expect(result.current[0]).toBe("default");
    expect(localStorage.getItem("test-key")).toBeNull();
  });

  it("handles JSON parse errors gracefully", () => {
    localStorage.setItem("test-key", "not-json");
    const { result } = renderHook(() =>
      useLocalStorage("test-key", "fallback"),
    );
    expect(result.current[0]).toBe("fallback");
  });
});
