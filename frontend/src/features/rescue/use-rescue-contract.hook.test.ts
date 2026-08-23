import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useRescueContract } from "./use-rescue-contract.hook";
import { tierThresholds } from "./rescue.config";
import { SubmitResponse } from "@/features/code-execution/code-execution.types";
import { rescueService } from "./rescue.service";

vi.mock("./rescue.service", () => ({
  rescueService: {
    getDue: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    abandon: vi.fn().mockResolvedValue(null),
    complete: vi.fn().mockResolvedValue(null),
    dismiss: vi.fn().mockResolvedValue(null),
  },
}));

const testCases = [
  { input: "1", expected_output: "2", description: "Sample A" },
  { input: "3", expected_output: "4", hidden: true },
  { input: "[1]", expected_output: "[]", description: "Edge" },
];

function makeSubmit(passedCount: number, total: number): SubmitResponse {
  return {
    passed: passedCount === total,
    total,
    passed_count: passedCount,
    results: Array.from({ length: total }, (_, i) => ({
      index: i + 1,
      passed: i < passedCount,
      input: String(i),
      expected: String(i),
      actual: i < passedCount ? String(i) : "wrong",
      hidden: false,
    })),
  };
}

describe("useRescueContract", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  const baseOptions: {
    questionId: string;
    questionTitle: string;
    testCases: typeof testCases;
    lastSubmitResult: SubmitResponse | null;
  } = {
    questionId: "q1",
    questionTitle: "Question One",
    testCases,
    lastSubmitResult: null,
  };

  it("does not fire before the T1 threshold", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1 - 1000);
    });
    expect(result.current.tier).toBe("none");
    expect(result.current.isStuck).toBe(false);
  });

  it("fires T1 once the T1 idle threshold is reached", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");
    expect(result.current.isStuck).toBe(true);
  });

  it("escalates T1 -> T2 -> T3 as idle time grows", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");

    act(() => {
      vi.advanceTimersByTime(tierThresholds.t2 - tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t2");

    act(() => {
      vi.advanceTimersByTime(tierThresholds.t3 - tierThresholds.t2);
    });
    expect(result.current.tier).toBe("t3");
  });

  it("resets to none on activity", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");

    act(() => {
      result.current.registerActivity();
    });
    expect(result.current.tier).toBe("none");
    expect(result.current.isStuck).toBe(false);
  });

  it("stops escalating when the problem is solved", () => {
    const { result, rerender } = renderHook(
      ({ opts }) => useRescueContract(opts),
      { initialProps: { opts: baseOptions } },
    );
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");

    rerender({
      opts: { ...baseOptions, lastSubmitResult: makeSubmit(3, 3) },
    });
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t3);
    });
    expect(result.current.tier).toBe("none");
  });

  it("honors the leave-me-alone toggle", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      result.current.leaveMeAlone();
    });
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t3);
    });
    expect(result.current.isSuppressed).toBe(true);
    expect(result.current.tier).toBe("none");
  });

  it("resumes after leave-me-alone", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      result.current.leaveMeAlone();
    });
    act(() => {
      result.current.resume();
    });
    expect(result.current.isSuppressed).toBe(false);
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");
  });

  it("does not count idle time while the tab is hidden", () => {
    const setVisibility = (state: "visible" | "hidden") => {
      Object.defineProperty(document, "visibilityState", {
        value: state,
        configurable: true,
      });
      document.dispatchEvent(
        new Event("visibilitychange"),
      );
    };
    setVisibility("hidden");
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t3);
    });
    expect(result.current.tier).toBe("none");

    setVisibility("visible");
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    expect(result.current.tier).toBe("t1");
  });

  it("builds checkpoints from test cases", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    const labels = result.current.checkpoints.map((c) => c.label);
    expect(labels).toEqual([
      "Run without error",
      "Sample A",
      "Edge",
      "Hidden cases → Solved",
    ]);
  });

  it("marks the failing checkpoint as current from submit results", () => {
    const { result } = renderHook(() =>
      useRescueContract({
        ...baseOptions,
        lastSubmitResult: {
          passed: false,
          total: 3,
          passed_count: 1,
          results: [
            { index: 1, passed: true, input: "1", expected: "2", actual: "2", hidden: false },
            { index: 2, passed: false, input: "[1]", expected: "[]", actual: "[1]", hidden: true },
            { index: 3, passed: false, input: "3", expected: "4", actual: "9", hidden: false },
          ],
        },
      }),
    );
    const current = result.current.checkpoints.find(
      (c) => c.state === "current",
    );
    expect(current).toBeDefined();
    // Visible test 1 ("Sample A") passes; visible test 2 ("Edge", position 3)
    // is the first failing visible checkpoint.
    expect(current?.label).toBe("Edge");
    expect(current?.detail).toContain("Expected:");
  });

  it("captures an abandoned problem on abandon", () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    act(() => {
      result.current.abandon();
    });
    const stored = JSON.parse(
      localStorage.getItem("rescue_abandoned_problems") || "[]",
    );
    expect(stored).toHaveLength(1);
    expect(stored[0].questionId).toBe("q1");
  });

  it("does not record an abandoned problem for solved work", () => {
    const { result, rerender } = renderHook(
      ({ opts }) => useRescueContract(opts),
      { initialProps: { opts: baseOptions } },
    );
    rerender({
      opts: { ...baseOptions, lastSubmitResult: makeSubmit(2, 2) },
    });
    act(() => {
      result.current.abandon();
    });
    const stored = JSON.parse(
      localStorage.getItem("rescue_abandoned_problems") || "[]",
    );
    expect(stored).toHaveLength(0);
  });

  it("notifies the durable rescue queue when abandoning", async () => {
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    await act(async () => {
      result.current.abandon();
    });
    expect(rescueService.abandon).toHaveBeenCalledWith(
      "q1",
      expect.any(Number),
    );
  });

  it("closes the durable queue item when the problem is solved", async () => {
    const { result, rerender } = renderHook(
      ({ opts }) => useRescueContract(opts),
      { initialProps: { opts: baseOptions } },
    );

    rerender({
      opts: { ...baseOptions, lastSubmitResult: makeSubmit(2, 2) },
    });

    await act(async () => {});
    expect(rescueService.complete).toHaveBeenCalledWith("q1");
  });

  it("keeps the local fallback capture even when the durable API fails", async () => {
    vi.mocked(rescueService.abandon).mockRejectedValueOnce(
      new Error("network down"),
    );
    const { result } = renderHook(() => useRescueContract(baseOptions));
    act(() => {
      vi.advanceTimersByTime(tierThresholds.t1);
    });
    await act(async () => {
      result.current.abandon();
    });
    const stored = JSON.parse(
      localStorage.getItem("rescue_abandoned_problems") || "[]",
    );
    expect(stored).toHaveLength(1);
  });
});
