import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { HttpError } from "@/lib/fetch-client";
import { useCurriculum, useCourse, useLesson } from "./use-curriculum.hook";

const mockGet = vi.hoisted(() => vi.fn());

vi.mock("@/lib/fetch-client", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/fetch-client")>();
  return {
    ...actual,
    FetchClient: vi.fn().mockImplementation(function () {
      return { get: mockGet };
    }),
  };
});

function serverError(detail: string): HttpError {
  return new HttpError(
    "Request failed: 500 Internal Server Error",
    500,
    JSON.stringify({ detail }),
  );
}

describe("curriculum hooks surface server error detail", () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it("useCurriculum renders server detail on course-list failure", async () => {
    mockGet.mockRejectedValue(serverError("Course catalog unavailable"));

    const { result } = renderHook(() => useCurriculum());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Course catalog unavailable");
  });

  it("useCourse renders server detail on course failure", async () => {
    mockGet.mockRejectedValue(serverError("Course not found"));

    const { result } = renderHook(() => useCourse("c1"));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Course not found");
  });

  it("useLesson renders server detail on lesson failure", async () => {
    mockGet.mockRejectedValue(serverError("Lesson is not published"));

    const { result } = renderHook(() => useLesson("l1"));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Lesson is not published");
  });

  it("useCurriculum keeps a generic fallback when the body is empty", async () => {
    mockGet.mockRejectedValue(new Error());

    const { result } = renderHook(() => useCurriculum());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Failed to load courses");
  });
});
