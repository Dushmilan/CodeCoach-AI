import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { AnimationScriptRenderer } from "./AnimationScriptRenderer";
import { AnimationPlayer } from "./AnimationPlayer";
import { AnimationScript } from "@/types";

const linearScript: AnimationScript = {
  type: "linear_search",
  title: "Searching for 4",
  data: { values: [5, 1, 2, 3, 4, 5], target: 4 },
  steps: [
    {
      operation: "compare",
      index: 0,
      result: "mismatch",
      narration: "5 is not the target.",
    },
    {
      operation: "compare",
      index: 1,
      result: "mismatch",
      narration: "1 is not the target.",
    },
    {
      operation: "compare",
      index: 4,
      result: "match",
      narration: "Found the target at index 4.",
    },
  ],
};

describe("AnimationScriptRenderer", () => {
  it("renders the animation title and target badge", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    expect(screen.getByText("Searching for 4")).toBeInTheDocument();
    expect(screen.getByText("Target")).toBeInTheDocument();
    expect(screen.getAllByText("4").length).toBeGreaterThan(0);
  });

  it("renders the array values as cells", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    for (const value of ["5", "1", "2", "3"]) {
      expect(screen.getAllByText(value).length).toBeGreaterThan(0);
    }
  });

  it("shows the narration of the first step initially", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    expect(screen.getByText("5 is not the target.")).toBeInTheDocument();
  });

  it("advances the narration when clicking next", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    fireEvent.click(screen.getByRole("button", { name: "Next step" }));
    expect(screen.getByText("1 is not the target.")).toBeInTheDocument();
    expect(screen.getByText(/2 \/ 3/)).toBeInTheDocument();
  });

  it("reaches the match narration on the last step", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    const next = screen.getByRole("button", { name: "Next step" });
    fireEvent.click(next);
    fireEvent.click(next);
    expect(screen.getByText("Found the target at index 4.")).toBeInTheDocument();
  });

  it("stops advancing at the final step", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    const next = screen.getByRole("button", { name: "Next step" });
    fireEvent.click(next);
    fireEvent.click(next);
    fireEvent.click(next);
    expect(screen.getByText(/3 \/ 3/)).toBeInTheDocument();
  });

  it("restart resets to the first step", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    const next = screen.getByRole("button", { name: "Next step" });
    fireEvent.click(next);
    fireEvent.click(next);
    fireEvent.click(screen.getByRole("button", { name: "Restart animation" }));
    expect(screen.getByText("5 is not the target.")).toBeInTheDocument();
    expect(screen.getByText(/1 \/ 3/)).toBeInTheDocument();
  });

  it("toggles play state", () => {
    render(<AnimationScriptRenderer script={linearScript} />);
    const play = screen.getByRole("button", { name: "Play animation" });
    fireEvent.click(play);
    expect(
      screen.getByRole("button", { name: "Pause animation" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Pause animation" }));
    expect(
      screen.getByRole("button", { name: "Play animation" }),
    ).toBeInTheDocument();
  });

  it("renders a plain trace for unsupported animation types", () => {
    const unknown: AnimationScript = {
      type: "quantum_sort",
      title: "Quantum",
      data: { values: [1, 2] },
      steps: [{ operation: "compare", index: 0, narration: "Narration one." }],
    };
    render(<AnimationScriptRenderer script={unknown} />);
    expect(screen.getByText("Quantum")).toBeInTheDocument();
    expect(screen.getByText("Narration one.")).toBeInTheDocument();
  });

  it("returns null when there are no steps", () => {
    const { container } = render(
      <AnimationScriptRenderer
        script={{ type: "linear_search", data: { values: [] }, steps: [] }}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("guards against a missing steps array", () => {
    const { container } = render(
      <AnimationScriptRenderer
        script={
          { type: "linear_search", data: { values: [] } } as unknown as AnimationScript
        }
      />,
    );
    expect(container.firstChild).toBeNull();
  });
});

describe("AnimationPlayer", () => {
  const steps = linearScript.steps;

  it("auto-advances while playing and auto-pauses on a match", () => {
    vi.useFakeTimers();
    try {
      render(
        <AnimationPlayer steps={steps}>
          {(step) => <div>{step.narration}</div>}
        </AnimationPlayer>,
      );
      act(() => {
        fireEvent.click(screen.getByRole("button", { name: "Play animation" }));
      });
      act(() => {
        vi.advanceTimersByTime(900);
      });
      expect(screen.getByText("1 is not the target.")).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(900);
      });
      expect(
        screen.getByText("Found the target at index 4."),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Play animation" }),
      ).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("restarts from the beginning when played at the final step", () => {
    vi.useFakeTimers();
    try {
      render(
        <AnimationPlayer steps={steps}>
          {(step) => <div>{step.narration}</div>}
        </AnimationPlayer>,
      );
      const next = screen.getByRole("button", { name: "Next step" });
      act(() => {
        fireEvent.click(next);
      });
      act(() => {
        fireEvent.click(next);
      });
      expect(screen.getByText("Found the target at index 4.")).toBeInTheDocument();
      act(() => {
        fireEvent.click(screen.getByRole("button", { name: "Play animation" }));
      });
      act(() => {
        vi.advanceTimersByTime(900);
      });
      expect(screen.getByText("1 is not the target.")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});
