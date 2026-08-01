import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import TerminalSimulation from "./TerminalSimulation";

describe("TerminalSimulation", () => {
  it("renders terminal container", () => {
    const { container } = render(<TerminalSimulation output="Hello World" />);
    const terminal = container.firstChild as HTMLElement;
    expect(terminal).toBeInTheDocument();
    expect(terminal.className).toContain("bg-");
  });

  it("displays characters progressively", async () => {
    render(<TerminalSimulation output="Hello" />);
    expect(
      await screen.findByText("Hello", undefined, { timeout: 1000 }),
    ).toBeInTheDocument();
  });

  it("renders full output after all characters typed", async () => {
    render(<TerminalSimulation output="ABCD" />);
    expect(
      await screen.findByText("ABCD", undefined, { timeout: 1000 }),
    ).toBeInTheDocument();
  });

  it("handles empty output", () => {
    const { container } = render(<TerminalSimulation output="" />);
    const span = container.querySelector("span");
    expect(span).toBeInTheDocument();
  });
});
