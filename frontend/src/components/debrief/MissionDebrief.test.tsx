import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MissionDebrief } from "./MissionDebrief";
import { DebriefFeature } from "@/features/debrief/debrief.types";

function makeProps(overrides: Partial<DebriefFeature> = {}): DebriefFeature {
  const base: DebriefFeature = {
    phase: "idle",
    context: null,
    currentQuestion: "",
    isTyping: false,
    reportLoading: false,
    round: 0,
    totalRounds: 3,
    isLastRound: false,
    report: null,
    openMissionComplete: vi.fn(),
    startDebrief: vi.fn().mockResolvedValue(undefined),
    submitExplanation: vi.fn().mockResolvedValue(undefined),
    submitNotSure: vi.fn().mockResolvedValue(undefined),
    finishDebrief: vi.fn().mockResolvedValue(undefined),
    closeDebrief: vi.fn(),
  };
  return { ...base, ...overrides };
}

describe("MissionDebrief", () => {
  it("renders nothing when idle", () => {
    const { container } = render(<MissionDebrief {...makeProps()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the mission-complete overlay and starts the debrief", async () => {
    const props = makeProps({ phase: "mission-complete" });
    render(<MissionDebrief {...props} />);

    expect(screen.getByText("Your solution works.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /start debrief/i }));
    expect(props.startDebrief).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: /skip debrief/i }));
    expect(props.closeDebrief).toHaveBeenCalledTimes(1);
  });

  it("renders the dialogue stage with the junior persona and question", () => {
    const props = makeProps({
      phase: "dialogue",
      context: {
        problem: "Two Sum",
        code: "def two_sum(): pass",
        language: "python",
      },
      currentQuestion: "Why a hashmap instead of two pointers?",
      round: 1,
    });
    render(<MissionDebrief {...props} />);

    expect(screen.getByText("Two Sum")).toBeInTheDocument();
    expect(screen.getByText("Milo, Junior Dev")).toBeInTheDocument();
    expect(
      screen.getByText("Why a hashmap instead of two pointers?"),
    ).toBeInTheDocument();
    expect(screen.getByText(/def two_sum/)).toBeInTheDocument();
    expect(screen.getByText("Question 2 of 3")).toBeInTheDocument();
  });

  it("submits an explanation through the dialogue", async () => {
    const props = makeProps({
      phase: "dialogue",
      context: { problem: "Two Sum", code: "code()", language: "python" },
      currentQuestion: "How does it work?",
      round: 0,
    });
    render(<MissionDebrief {...props} />);

    await userEvent.type(
      screen.getByPlaceholderText(/why did you write it this way/),
      "I used a hashmap for O(n) lookups.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Submit Explanation" }));
    expect(props.submitExplanation).toHaveBeenCalledWith(
      "I used a hashmap for O(n) lookups.",
    );
  });

  it("triggers onNotSure via the I'm not sure button", async () => {
    const props = makeProps({
      phase: "dialogue",
      context: { problem: "Two Sum", code: "code()", language: "python" },
      currentQuestion: "What's the complexity?",
      round: 0,
    });
    render(<MissionDebrief {...props} />);

    await userEvent.click(screen.getByRole("button", { name: /i'm not sure/i }));
    expect(props.submitNotSure).toHaveBeenCalledTimes(1);
  });

  it("shows the report button on the last round", async () => {
    const props = makeProps({
      phase: "dialogue",
      context: { problem: "Two Sum", code: "code()", language: "python" },
      currentQuestion: "Final question?",
      round: 3,
      isLastRound: true,
    });
    render(<MissionDebrief {...props} />);

    await userEvent.click(screen.getByRole("button", { name: /view debrief report/i }));
    expect(props.finishDebrief).toHaveBeenCalledTimes(1);
  });

  it("renders the report with per-exchange feedback and continues", async () => {
    const props = makeProps({
      phase: "report",
      report: {
        summary: "A solid session.",
        exchanges: [
          {
            question: "Why a hashmap?",
            answer: "For O(1) lookups.",
            strengths: ["Identified the right data structure"],
            improvements: ["Mention the memory tradeoff"],
            strongerAnswer: ["Space complexity"],
          },
        ],
        takeaway: "Teaching is learning.",
      },
    });
    render(<MissionDebrief {...props} />);

    expect(screen.getByText("Mission Debrief")).toBeInTheDocument();
    expect(screen.getByText("A solid session.")).toBeInTheDocument();
    expect(screen.getByText("Why a hashmap?")).toBeInTheDocument();
    expect(screen.getByText(/O\(1\) lookups/)).toBeInTheDocument();
    expect(screen.getByText("Identified the right data structure")).toBeInTheDocument();
    expect(screen.getByText("Mention the memory tradeoff")).toBeInTheDocument();
    expect(screen.getByText("A stronger answer would include")).toBeInTheDocument();
    expect(screen.getByText("Space complexity")).toBeInTheDocument();
    expect(screen.getByText("Teaching is learning.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /continue learning/i }));
    expect(props.closeDebrief).toHaveBeenCalledTimes(1);
  });

  it("shows a loading state while the report is being generated", () => {
    const props = makeProps({
      phase: "report",
      reportLoading: true,
      report: {
        summary: "",
        exchanges: [],
        takeaway: "",
      },
    });
    render(<MissionDebrief {...props} />);

    expect(screen.getByText("Assessing your answers…")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /continue learning/i }),
    ).toBeDisabled();
  });
});
