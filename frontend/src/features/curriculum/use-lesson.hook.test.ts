import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useLesson } from "./use-curriculum.hook";

const mockGet = vi.hoisted(() => vi.fn());

vi.mock("@/lib/fetch-client", () => ({
  FetchClient: vi.fn().mockImplementation(function () {
    return { get: mockGet };
  }),
}));

describe("useLesson", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("returns loading state initially", () => {
    mockGet.mockResolvedValue({ id: "1", title: "Test" });
    const { result } = renderHook(() => useLesson("1"));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.lesson).toBeNull();
  });

  it("fetches and returns lesson data", async () => {
    const lessonData = { id: "1", title: "Test Lesson", content: "Content" };
    mockGet.mockResolvedValue(lessonData);

    const { result } = renderHook(() => useLesson("1"));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.lesson).toEqual(lessonData);
    expect(mockGet).toHaveBeenCalledWith("/api/courses/lessons/1");
  });

  it("sets error when fetch fails", async () => {
    mockGet.mockRejectedValue(new Error("Failed to load"));

    const { result } = renderHook(() => useLesson("1"));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.lesson).toBeNull();
    expect(result.current.error).toBe("Failed to load");
  });

  it("refetches lesson data", async () => {
    mockGet.mockResolvedValue({ id: "1", title: "Initial" });

    const { result } = renderHook(() => useLesson("1"));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.lesson?.title).toBe("Initial");

    mockGet.mockResolvedValue({ id: "1", title: "Updated" });
    result.current.refetch();

    await waitFor(() => expect(result.current.lesson?.title).toBe("Updated"));
  });

  it("does nothing when lessonId is empty", () => {
    const { result } = renderHook(() => useLesson(""));
    expect(result.current.isLoading).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});
