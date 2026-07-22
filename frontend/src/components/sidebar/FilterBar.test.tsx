import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FilterBar } from "./FilterBar";

describe("FilterBar", () => {
  const defaultProps = {
    currentFilter: "all" as const,
    onFilterChange: vi.fn(),
    onAll: vi.fn(),
    onRandom: vi.fn(),
  };

  it("renders All and Random buttons", () => {
    render(<FilterBar {...defaultProps} />);
    expect(screen.getByRole("button", { name: /all/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /random/i })).toBeInTheDocument();
  });

  it("renders difficulty filter buttons", () => {
    render(<FilterBar {...defaultProps} />);
    expect(screen.getByRole("button", { name: /easy/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /medium/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hard/i })).toBeInTheDocument();
  });

  it("applies active styles to All button when currentFilter is all", () => {
    render(<FilterBar {...defaultProps} currentFilter="all" />);
    const allBtn = screen.getByRole("button", { name: /all/i });
    expect(allBtn.className).toContain("bg-primary");
  });

  it("applies green color to easy button when currentFilter is easy", () => {
    render(<FilterBar {...defaultProps} currentFilter="easy" />);
    const btn = screen.getByRole("button", { name: /easy/i });
    expect(btn.className).toContain("text-green-400");
  });

  it("applies yellow color to medium button when currentFilter is medium", () => {
    render(<FilterBar {...defaultProps} currentFilter="medium" />);
    const btn = screen.getByRole("button", { name: /medium/i });
    expect(btn.className).toContain("text-yellow-400");
  });

  it("applies red color to hard button when currentFilter is hard", () => {
    render(<FilterBar {...defaultProps} currentFilter="hard" />);
    const btn = screen.getByRole("button", { name: /hard/i });
    expect(btn.className).toContain("text-red-400");
  });

  it("calls onAll when All is clicked", async () => {
    const onAll = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onAll={onAll} />);
    await user.click(screen.getByRole("button", { name: /all/i }));
    expect(onAll).toHaveBeenCalledOnce();
  });

  it("calls onRandom when Random is clicked", async () => {
    const onRandom = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onRandom={onRandom} />);
    await user.click(screen.getByRole("button", { name: /random/i }));
    expect(onRandom).toHaveBeenCalledOnce();
  });

  it("calls onFilterChange with correct difficulty", async () => {
    const onFilterChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onFilterChange={onFilterChange} />);
    await user.click(screen.getByRole("button", { name: /medium/i }));
    expect(onFilterChange).toHaveBeenCalledWith("medium");
  });

  it("hides content when collapsed", () => {
    const { container } = render(<FilterBar {...defaultProps} isCollapsed />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain("opacity-0");
    expect(outerDiv.className).toContain("h-0");
  });
});
