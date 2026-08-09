import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { UpgradeModal } from "./UpgradeModal";

describe("UpgradeModal", () => {
  it("renders the plan comparison and CTA", () => {
    render(<UpgradeModal open onClose={vi.fn()} />);
    expect(
      screen.getByRole("heading", { name: /upgrade to pro/i }),
    ).toBeTruthy();
    expect(screen.getByText(/request access/i)).toBeTruthy();
  });

  it("renders the free and pro tiers", () => {
    render(<UpgradeModal open onClose={vi.fn()} />);
    expect(screen.getByText("Free")).toBeTruthy();
    expect(screen.getByText("Pro")).toBeTruthy();
  });

  it("does not render when closed", () => {
    const { container } = render(<UpgradeModal open={false} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it("calls onClose when dismissed", () => {
    const onClose = vi.fn();
    render(<UpgradeModal open onClose={onClose} />);
    screen.getByRole("button", { name: /close/i }).click();
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});