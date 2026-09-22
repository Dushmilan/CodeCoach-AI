import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { CodePane } from "./CodePane";

const CODE = ["def total(values):", "    acc = 0", "    return acc"].join("\n");

describe("CodePane", () => {
  afterEach(() => {
    // scrollIntoView is unimplemented in jsdom; the pane guards with `?.`.
    // Clean up any prototype stub a test installed.
    delete (HTMLElement.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  });

  it("renders every code line with its line number", () => {
    render(<CodePane code={CODE} />);
    expect(screen.getByTestId("code-pane")).toBeInTheDocument();
    expect(screen.getByText("def total(values):")).toBeInTheDocument();
    expect(screen.getByText("acc = 0")).toBeInTheDocument();
    expect(screen.getByText("return acc")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("marks exactly the active line", () => {
    const { container } = render(<CodePane code={CODE} activeLine={2} />);
    const active = container.querySelectorAll("[data-active-line='true']");
    expect(active).toHaveLength(1);
    expect(active[0].textContent).toContain("acc = 0");
  });

  it("renders nothing without code", () => {
    const { container } = render(<CodePane />);
    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId("code-pane")).toBeNull();
  });

  it("highlights nothing for an out-of-range active line", () => {
    const { container } = render(<CodePane code={CODE} activeLine={99} />);
    expect(
      container.querySelectorAll("[data-active-line='true']"),
    ).toHaveLength(0);
    // Every line still renders — the pane never hides content.
    expect(screen.getByText("return acc")).toBeInTheDocument();
  });

  it("ignores a null active line (beats without a traced line)", () => {
    const { container } = render(<CodePane code={CODE} activeLine={null} />);
    expect(
      container.querySelectorAll("[data-active-line='true']"),
    ).toHaveLength(0);
  });

  it("scrolls the active line into view", () => {
    const scrollSpy = vi.fn();
    (
      HTMLElement.prototype as unknown as { scrollIntoView: unknown }
    ).scrollIntoView = scrollSpy;
    render(<CodePane code={CODE} activeLine={3} />);
    expect(scrollSpy).toHaveBeenCalledTimes(1);
    expect(scrollSpy).toHaveBeenCalledWith({ block: "nearest" });
  });
});
