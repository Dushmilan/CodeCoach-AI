import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SolvedTakeover } from "./SolvedTakeover";

const readyBeats = [
  "Compare first and last values",
  "Discard the half that cannot hold the answer",
  "Repeat on the remaining window",
  "Return the match index",
];

describe("SolvedTakeover", () => {
  it("renders title, stats, and replay beats when ready", () => {
    render(
      <SolvedTakeover
        open
        onClose={() => {}}
        questionTitle="Two Sum"
        difficulty="easy"
        passed={3}
        total={3}
        replay={{ status: "ready", beats: readyBeats }}
        onNext={() => {}}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Two Sum")).toBeInTheDocument();
    expect(screen.getByText(/3 of 3 passed/)).toBeInTheDocument();
    for (const beat of readyBeats) {
      expect(screen.getByText(beat)).toBeInTheDocument();
    }
    expect(
      screen.getByRole("button", { name: /next question/i }),
    ).toBeInTheDocument();
  });

  it("shows loading skeleton while replay compiles", () => {
    render(
      <SolvedTakeover
        open
        onClose={() => {}}
        questionTitle="Two Sum"
        difficulty="easy"
        passed={3}
        total={3}
        replay={{ status: "loading" }}
        onNext={() => {}}
      />,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows retry affordance on replay error", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(
      <SolvedTakeover
        open
        onClose={() => {}}
        questionTitle="Two Sum"
        difficulty="easy"
        passed={3}
        total={3}
        replay={{ status: "error", message: "Replay failed" }}
        onNext={() => {}}
        onRetry={onRetry}
      />,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("renders nothing interactive when closed", () => {
    render(
      <SolvedTakeover
        open={false}
        onClose={() => {}}
        questionTitle="Two Sum"
        difficulty="easy"
        passed={3}
        total={3}
        replay={{ status: "ready", beats: readyBeats }}
        onNext={() => {}}
      />,
    );

    expect(screen.queryByText("Two Sum")).not.toBeInTheDocument();
  });
});
