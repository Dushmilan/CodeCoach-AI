import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useDebrief, sanitizeSeniorQuestion } from "./use-debrief.hook";
import { ChatMessage } from "@/types";

const { mockGetDebriefReport } = vi.hoisted(() => ({
  mockGetDebriefReport: vi.fn(),
}));

vi.mock("@/features/coaching/coaching.service", () => ({
  coachingService: {
    getDebriefReport: (...args: unknown[]) => mockGetDebriefReport(...args),
  },
}));

function makeMessages(contents: string[]): ChatMessage[] {
  return contents.map((content, i) => ({
    id: `${i}`,
    role: (i % 2 === 0 ? "assistant" : "user") as "assistant" | "user",
    content,
    timestamp: new Date(),
  }));
}

function setup() {
  const sendMessage = vi.fn().mockResolvedValue(undefined);
  let messages: ChatMessage[] = [];
  const props = {
    messages,
    isTyping: false,
    sendMessage,
  };
  const { result, rerender } = renderHook(
    (p) => useDebrief(p),
    { initialProps: props },
  );
  return {
    result,
    rerender,
    sendMessage,
    setMessages: (m: ChatMessage[]) => rerender({ ...props, messages: m }),
    setTyping: (t: boolean) => rerender({ ...props, isTyping: t }),
  };
}

function makeReport() {
  return {
    summary: "You explained your approach clearly.",
    exchanges: [
      {
        question: "Why a hashmap?",
        answer: "For O(1) lookups.",
        strengths: ["Identified the right data structure"],
        improvements: ["Mention the memory tradeoff"],
        strongerAnswer: ["Space complexity", "Edge case: empty input"],
      },
    ],
    takeaway: "Always justify space too.",
  };
}

beforeEach(() => {
  mockGetDebriefReport.mockReset();
});

describe("useDebrief", () => {
  it("starts idle with no context", () => {
    const { result } = setup();
    expect(result.current.phase).toBe("idle");
    expect(result.current.context).toBeNull();
  });

  it("opens mission-complete with the supplied context", () => {
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "def two_sum(): pass",
        language: "python",
      });
    });
    expect(result.current.phase).toBe("mission-complete");
    expect(result.current.context?.problem).toBe("Two Sum");
    expect(result.current.round).toBe(0);
  });

  it("startDebrief moves to dialogue and sends an opening senior message", async () => {
    const { result, sendMessage } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "def two_sum(): pass",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    expect(result.current.phase).toBe("dialogue");
    expect(sendMessage).toHaveBeenCalledWith(
      expect.any(String),
      "senior",
      "Two Sum",
      "def two_sum(): pass",
      "python",
    );
  });

  it("submitExplanation sends the text in senior mode and advances the round", async () => {
    const { result, sendMessage } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitExplanation("I used a hashmap to get O(n) lookups.");
    });
    expect(sendMessage).toHaveBeenLastCalledWith(
      "I used a hashmap to get O(n) lookups.",
      "senior",
      "Two Sum",
      "code()",
      "python",
    );
    expect(result.current.round).toBe(1);
  });

  it("submitNotSure captures the exchange and advances the round", async () => {
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitNotSure();
    });
    expect(result.current.round).toBe(1);
  });

  it("reports isLastRound once all rounds are completed", async () => {
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    for (let i = 0; i < result.current.totalRounds; i++) {
      await act(async () => {
        await result.current.submitExplanation(`Answer number ${i + 1} with enough detail.`);
      });
    }
    expect(result.current.round).toBe(result.current.totalRounds);
    expect(result.current.isLastRound).toBe(true);
  });

  it("currentQuestion returns the latest assistant message from the debrief session", async () => {
    const { result, setMessages } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    setMessages(
      makeMessages([
        "walk me through this",
        "I used a hashmap",
        "why a hashmap instead of two pointers?",
      ]),
    );
    expect(result.current.currentQuestion).toBe(
      "why a hashmap instead of two pointers?",
    );
  });

  it("currentQuestion is empty before the debrief starts", () => {
    const { result, setMessages } = setup();
    setMessages(makeMessages(["some old assistant message"]));
    expect(result.current.currentQuestion).toBe("");
  });

  it("finishDebrief builds a report and moves to report phase", async () => {
    mockGetDebriefReport.mockResolvedValue(makeReport());
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitExplanation("I used a hashmap for O(n) lookups.");
    });
    await act(async () => {
      await result.current.finishDebrief();
    });
    expect(result.current.phase).toBe("report");
    expect(result.current.reportLoading).toBe(false);
    expect(result.current.report).not.toBeNull();
    expect(result.current.report?.summary).toBe("You explained your approach clearly.");
    expect(result.current.report?.exchanges.length).toBe(1);
    expect(result.current.report?.exchanges[0].question).toBe("Why a hashmap?");
    expect(result.current.report?.takeaway.length).toBeGreaterThan(0);
  });

  it("finishDebrief sends the captured exchanges to the report endpoint", async () => {
    mockGetDebriefReport.mockResolvedValue(makeReport());
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitExplanation("I used a hashmap for O(n) lookups.");
    });
    await act(async () => {
      await result.current.finishDebrief();
    });
    expect(mockGetDebriefReport).toHaveBeenCalledWith(
      "Two Sum",
      "python",
      "code()",
      [
        {
          question: "Explain this part of your code.",
          answer: "I used a hashmap for O(n) lookups.",
        },
      ],
    );
  });

  it("finishDebrief falls back to a local report when the API fails", async () => {
    mockGetDebriefReport.mockRejectedValue(new Error("network down"));
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitExplanation("I used a hashmap for O(n) lookups.");
    });
    await act(async () => {
      await result.current.finishDebrief();
    });
    expect(result.current.report).not.toBeNull();
    expect(result.current.report?.summary.length).toBeGreaterThan(0);
    expect(result.current.report?.exchanges).toHaveLength(1);
  });

  it("finishDebrief keeps captured exchanges when the API returns an empty report", async () => {
    mockGetDebriefReport.mockResolvedValue({
      summary: "Done.",
      exchanges: [],
      takeaway: "",
    });
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    await act(async () => {
      await result.current.startDebrief();
    });
    await act(async () => {
      await result.current.submitExplanation("I used a hashmap for O(n) lookups.");
    });
    await act(async () => {
      await result.current.finishDebrief();
    });
    expect(result.current.report?.exchanges).toHaveLength(1);
    expect(result.current.report?.exchanges[0].answer).toBe(
      "I used a hashmap for O(n) lookups.",
    );
    expect(result.current.report?.exchanges[0].strongerAnswer).toEqual([]);
    expect(result.current.report?.summary).toBe("Done.");
  });

  it("closeDebrief resets to idle", async () => {
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "Two Sum",
        code: "code()",
        language: "python",
      });
    });
    act(() => {
      result.current.closeDebrief();
    });
    expect(result.current.phase).toBe("idle");
    expect(result.current.context).toBeNull();
    expect(result.current.report).toBeNull();
  });

  it("clears report when reopening mission complete", () => {
    const { result } = setup();
    act(() => {
      result.current.openMissionComplete({
        problem: "A",
        code: "c",
        language: "python",
      });
    });
    act(() => {
      result.current.closeDebrief();
    });
    act(() => {
      result.current.openMissionComplete({
        problem: "B",
        code: "d",
        language: "python",
      });
    });
    expect(result.current.report).toBeNull();
    expect(result.current.round).toBe(0);
  });
});

describe("sanitizeSeniorQuestion", () => {
  it("returns the first sentence only", () => {
    expect(
      sanitizeSeniorQuestion(
        "How does your solution handle duplicates? And what about the time complexity?",
      ),
    ).toBe("How does your solution handle duplicates?");
  });

  it("keeps a single-sentence question intact", () => {
    expect(sanitizeSeniorQuestion("Why did you choose a hashmap?")).toBe(
      "Why did you choose a hashmap?",
    );
  });

  it("strips leading and trailing whitespace", () => {
    expect(sanitizeSeniorQuestion("  What made you pick this approach?  ")).toBe(
      "What made you pick this approach?",
    );
  });

  it("handles an empty string", () => {
    expect(sanitizeSeniorQuestion("")).toBe("");
  });

  it("handles whitespace-only input", () => {
    expect(sanitizeSeniorQuestion("   ")).toBe("");
  });

  it("returns the whole message when it has no sentence punctuation", () => {
    expect(sanitizeSeniorQuestion("Why a hashmap")).toBe("Why a hashmap");
  });
});
