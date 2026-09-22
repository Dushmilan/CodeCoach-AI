import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { AnimationPlayer } from "./AnimationPlayer";

const steps = [{ narration: "One" }, { narration: "Two" }, { narration: "Three" }];

describe("AnimationPlayer scrub", () => {
  it("scrubs via slider and announces narration", () => {
    render(<AnimationPlayer steps={steps as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>);
    fireEvent.change(screen.getByRole("slider", { name: /animation progress/i }), { target: { value: "2" } });
    expect(screen.getByText("Three")).toBeInTheDocument();
  });
});

describe("AnimationPlayer auto-advance", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("waits for the longest motion in the beat before advancing", () => {
    vi.useFakeTimers();
    const timed = [
      { narration: "One", motion: [{ target: "a", op: "fill", to: "#1d4ed8", duration: 0.9 }] },
      { narration: "Two" },
    ];
    render(<AnimationPlayer steps={timed as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>);
    fireEvent.click(screen.getByRole("button", { name: /play/i }));
    // Default Normal speed is 800ms but the beat needs 900ms: still on "One".
    act(() => {
      vi.advanceTimersByTime(800);
    });
    expect(screen.getByText("One")).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(screen.getByText("Two")).toBeInTheDocument();
  });

  it("falls back to the speed preset when the beat has no motion", () => {
    vi.useFakeTimers();
    render(<AnimationPlayer steps={steps as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>);
    fireEvent.click(screen.getByRole("button", { name: /play/i }));
    act(() => {
      vi.advanceTimersByTime(800);
    });
    expect(screen.getByText("Two")).toBeInTheDocument();
  });

  it("clamps the index when a shorter script replaces the steps", () => {
    // #240 browser pass: switching scripts (e.g. planner → fallback) left
    // currentIndex past the end, rendering a blank scene with counter N/M.
    const { rerender } = render(
      <AnimationPlayer steps={steps as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>,
    );
    fireEvent.change(screen.getByRole("slider", { name: /animation progress/i }), { target: { value: "2" } });
    expect(screen.getByText("Three")).toBeInTheDocument();
    rerender(
      <AnimationPlayer steps={[{ narration: "Solo" }] as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>,
    );
    expect(screen.getByText("Solo")).toBeInTheDocument();
    expect(screen.getByText("1 / 1")).toBeInTheDocument();
  });
});
