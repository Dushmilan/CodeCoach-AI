import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import TerminalSimulation from "./TerminalSimulation";

describe("TerminalSimulation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders terminal container", () => {
    const { container } = render(<TerminalSimulation output="Hello World" />);
    const terminal = container.firstChild as HTMLElement;
    expect(terminal).toBeInTheDocument();
    expect(terminal.className).toContain("bg-");
  });

  it("displays characters progressively", () => {
    render(<TerminalSimulation output="Hello" />);
    act(() => {
      vi.advanceTimersByTime(15);
    });
    expect(screen.getByText("H")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(60);
    });
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders full output after all characters typed", () => {
    render(<TerminalSimulation output="ABCD" />);
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(screen.getByText("ABCD")).toBeInTheDocument();
  });

  it("handles empty output", () => {
    render(<TerminalSimulation output="" />);
    act(() => {
      vi.advanceTimersByTime(100);
    });
    const container = screen.getByText(
      (_, element) => element?.tagName === "SPAN",
    );
    expect(container).toBeInTheDocument();
  });
});
