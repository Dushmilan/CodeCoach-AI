import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { UsageBar } from "./UsageBar";

describe("UsageBar", () => {
  it("renders used and limit counts", () => {
    render(
      <UsageBar
        usage={{
          plan: "free",
          daily_limit: 20,
          daily_used: 15,
          daily_remaining: 5,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
        onUpgrade={vi.fn()}
      />,
    );
    expect(screen.getByText(/15 \/ 20/)).toBeTruthy();
  });

  it("shows an Upgrade button for free users", () => {
    render(
      <UsageBar
        usage={{
          plan: "free",
          daily_limit: 20,
          daily_used: 5,
          daily_remaining: 15,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
        onUpgrade={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /upgrade/i })).toBeTruthy();
  });

  it("does not show an Upgrade button for pro users", () => {
    render(
      <UsageBar
        usage={{
          plan: "pro",
          daily_limit: 500,
          daily_used: 10,
          daily_remaining: 490,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
        onUpgrade={vi.fn()}
      />,
    );
    expect(screen.queryByRole("button", { name: /upgrade/i })).toBeNull();
  });

  it("invokes onUpgrade when the Upgrade button is clicked", () => {
    const onUpgrade = vi.fn();
    render(
      <UsageBar
        usage={{
          plan: "free",
          daily_limit: 20,
          daily_used: 5,
          daily_remaining: 15,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
        onUpgrade={onUpgrade}
      />,
    );
    screen.getByRole("button", { name: /upgrade/i }).click();
    expect(onUpgrade).toHaveBeenCalledTimes(1);
  });

  it("renders nothing when usage is not loaded", () => {
    const { container } = render(<UsageBar usage={null} onUpgrade={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });
});