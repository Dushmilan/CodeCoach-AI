import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DebriefReportView } from "./DebriefReport";
import { DebriefReport } from "@/features/debrief/debrief.types";

function makeReport(exchanges: DebriefReport["exchanges"] = []): DebriefReport {
  return {
    summary: "A solid session.",
    exchanges,
    takeaway: "Teaching is learning.",
  };
}

const noop = () => {};

describe("DebriefReportView", () => {
  it("shows the header, summary, exchange count and takeaway", () => {
    render(
      <DebriefReportView
        report={makeReport()}
        loading={false}
        onClose={noop}
      />,
    );

    expect(screen.getByText("Mission Debrief")).toBeInTheDocument();
    expect(screen.getByText("A solid session.")).toBeInTheDocument();
    expect(screen.getByText("Teaching is learning.")).toBeInTheDocument();
  });

  it("renders the exchange count when there are exchanges", () => {
    const report = makeReport([
      {
        question: "Why a hashmap?",
        answer: "For O(1) lookups.",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getByText("1 exchange reviewed")).toBeInTheDocument();
  });

  it("renders question and quoted answer for each exchange", () => {
    const report = makeReport([
      {
        question: "Why a hashmap?",
        answer: "For O(1) lookups.",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getByText("Why a hashmap?")).toBeInTheDocument();
    expect(screen.getByText(/O\(1\) lookups/)).toBeInTheDocument();
  });

  it("renders overview and exchange nav chips", () => {
    const report = makeReport([
      {
        question: "Q1",
        answer: "A1",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
      {
        question: "Q2",
        answer: "A2",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Q1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Q2" })).toBeInTheDocument();
  });

  it("always shows Milo's Feedback and an empty-state message when every list is empty", () => {
    const report = makeReport([
      {
        question: "Why a hashmap?",
        answer: "For O(1) lookups.",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getAllByText("Milo's Feedback")).toHaveLength(1);
    expect(screen.getByText("AI review")).toBeInTheDocument();
    expect(screen.getByText("Not assessed")).toBeInTheDocument();
    expect(screen.queryByText("Answered well")).not.toBeInTheDocument();
    expect(screen.queryByText("What to improve")).not.toBeInTheDocument();
    expect(
      screen.queryByText("A stronger answer would include"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/couldn't assess this answer/i),
    ).toBeInTheDocument();
  });

  it("renders AI critique for a wrong answer with a needs-work badge", () => {
    const report = makeReport([
      {
        question: "Why a hashmap?",
        answer: "Because arrays are slow.",
        strengths: [],
        improvements: ["A hashmap gives O(1) average lookups"],
        strongerAnswer: ["Mention amortized O(1)"],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getAllByText("Milo's Feedback")).toHaveLength(1);
    expect(screen.getByText("Needs work")).toBeInTheDocument();
    expect(
      screen.getByText("A hashmap gives O(1) average lookups"),
    ).toBeInTheDocument();
    expect(screen.getByText("Mention amortized O(1)")).toBeInTheDocument();
  });

  it("renders AI critique for an unsure answer", () => {
    const report = makeReport([
      {
        question: "What about space?",
        answer: "I'm not sure.",
        strengths: [],
        improvements: ["Space is O(n) for the hashmap"],
        strongerAnswer: ["Talk through the tradeoff"],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getByText(/I'm not sure/)).toBeInTheDocument();
    expect(
      screen.getByText("Space is O(n) for the hashmap"),
    ).toBeInTheDocument();
  });

  it("renders strengths, improvements and stronger-answer sections when present", () => {
    const report = makeReport([
      {
        question: "Why a hashmap?",
        answer: "For O(1) lookups.",
        strengths: ["Right structure"],
        improvements: ["Mention space"],
        strongerAnswer: ["Space complexity"],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    expect(screen.getByText("Right structure")).toBeInTheDocument();
    expect(screen.getByText("Mention space")).toBeInTheDocument();
    expect(
      screen.getByText("A stronger answer would include"),
    ).toBeInTheDocument();
    expect(screen.getByText("Space complexity")).toBeInTheDocument();
    expect(screen.getByText("Good start")).toBeInTheDocument();
  });

  it("renders each exchange in order", () => {
    const report = makeReport([
      {
        question: "Q1",
        answer: "A1",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
      {
        question: "Q2",
        answer: "A2",
        strengths: [],
        improvements: [],
        strongerAnswer: [],
      },
    ]);
    render(
      <DebriefReportView report={report} loading={false} onClose={noop} />,
    );

    const questions = screen
      .getAllByTestId("debrief-question")
      .map((q) => q.textContent);
    expect(questions).toEqual(["Q1", "Q2"]);
  });

  it("shows a loading skeleton and disables continue while generating", () => {
    render(
      <DebriefReportView
        report={makeReport()}
        loading={true}
        onClose={noop}
      />,
    );

    expect(screen.getByText("Assessing your answers…")).toBeInTheDocument();
    expect(screen.getByText(/reviewing exchange/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /continue learning/i }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: /close report/i })).toBeDisabled();
    expect(screen.queryByText("A solid session.")).not.toBeInTheDocument();
  });

  it("calls onClose when Continue Learning is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <DebriefReportView
        report={makeReport()}
        loading={false}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: /continue learning/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <DebriefReportView
        report={makeReport()}
        loading={false}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: /close report/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <DebriefReportView
        report={makeReport()}
        loading={false}
        onClose={onClose}
      />,
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not close on Escape while loading", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <DebriefReportView
        report={makeReport()}
        loading={true}
        onClose={onClose}
      />,
    );

    await user.keyboard("{Escape}");
    expect(onClose).not.toHaveBeenCalled();
  });

  it("renders an accessible dialog", () => {
    render(
      <DebriefReportView
        report={makeReport()}
        loading={false}
        onClose={noop}
      />,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAccessibleName("A solid session.");
  });
});
