import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { UsageBar } from "./UsageBar";

describe("UsageBar", () => {
  it("renders used and limit counts", () => {
    render(
      <UsageBar
        usage={{
          daily_limit: 20,
          daily_used: 15,
          daily_remaining: 5,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
      />,
    );
    expect(screen.getByText(/15 \/ 20/)).toBeTruthy();
  });

  it("shows remaining today with no upgrade affordance", () => {
    render(
      <UsageBar
        usage={{
          daily_limit: 20,
          daily_used: 5,
          daily_remaining: 15,
          reset_at: "2026-08-07T00:00:00+00:00",
        }}
      />,
    );
    expect(screen.getByText(/15 remaining today/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /upgrade/i })).toBeNull();
  });

  it("renders null without usage", () => {
    const { container } = render(<UsageBar usage={null} />);
    expect(container.innerHTML).toBe("");
  });
});
