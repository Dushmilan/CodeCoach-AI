import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useCurriculum } from "./use-curriculum.hook";
import { FetchClient } from "@/lib/fetch-client";

// Mock FetchClient
vi.mock("@/lib/fetch-client", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/fetch-client")>();
  const MockFetchClient = vi.fn(function FetchClient() {
    return {
      get: vi.fn(),
      post: vi.fn(),
    };
  });
  return { ...actual, FetchClient: MockFetchClient };
});

function mockInstance() {
  return (FetchClient as any).mock.results[0].value;
}

beforeEach(() => {
  mockInstance().get.mockClear();
});

describe("useCurriculum learn view (issue #268)", () => {
  it("fetches the minimal learn summary in a single request", async () => {
    mockInstance().get.mockResolvedValue({
      courses: [
        {
          id: "1",
          title: "Test",
          description: "Desc",
          language: "python",
          progress: 50,
          completed_lessons_count: 1,
          last_accessed_lesson_id: "l1",
        },
      ],
    });

    const { result } = renderHook(() => useCurriculum());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const calls = mockInstance().get.mock.calls;
    expect(calls).toHaveLength(1);
    expect(calls[0][0]).toBe("/api/courses/?view=learn");
    expect(result.current.courses).toEqual([
      {
        id: "1",
        title: "Test",
        description: "Desc",
        language: "python",
        progress: 50,
        completed_lessons_count: 1,
        last_accessed_lesson_id: "l1",
      },
    ]);
  });

  it("dedupes concurrent mounts into one request", async () => {
    let resolveGet!: (v: unknown) => void;
    mockInstance().get.mockReturnValue(
      new Promise((resolve) => {
        resolveGet = resolve;
      }),
    );

    const first = renderHook(() => useCurriculum());
    const second = renderHook(() => useCurriculum());
    resolveGet({ courses: [] });

    await waitFor(() => expect(first.result.current.isLoading).toBe(false));
    await waitFor(() => expect(second.result.current.isLoading).toBe(false));

    const courseCalls = mockInstance().get.mock.calls.filter((c: unknown[]) =>
      String(c[0]).includes("/api/courses"),
    );
    expect(courseCalls).toHaveLength(1);
  });
});
