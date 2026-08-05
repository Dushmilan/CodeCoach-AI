import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { PremiumGate } from "./PremiumGate";

const mockUseAuth = vi.hoisted(() => vi.fn());

vi.mock("@/providers", () => ({ useAuth: mockUseAuth }));

describe("PremiumGate", () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
  });

  it("renders children when user has premium plan", () => {
    mockUseAuth.mockReturnValue({
      user: { plan: "premium" },
      isHydrated: true,
    });
    render(
      <PremiumGate>
        <span>premium content</span>
      </PremiumGate>,
    );
    expect(screen.getByText("premium content")).toBeInTheDocument();
  });

  it("renders upsell when user has free plan", () => {
    mockUseAuth.mockReturnValue({
      user: { plan: "free" },
      isHydrated: true,
    });
    render(
      <PremiumGate>
        <span>premium content</span>
      </PremiumGate>,
    );
    expect(screen.queryByText("premium content")).toBeNull();
    expect(
      screen.getByText("AI Coach is a Premium feature"),
    ).toBeInTheDocument();
  });

  it("renders upsell when no user is signed in", () => {
    mockUseAuth.mockReturnValue({ user: null, isHydrated: true });
    render(
      <PremiumGate>
        <span>premium content</span>
      </PremiumGate>,
    );
    expect(screen.queryByText("premium content")).toBeNull();
    expect(
      screen.getByText("AI Coach is a Premium feature"),
    ).toBeInTheDocument();
  });

  it("renders a custom fallback instead of the default upsell", () => {
    mockUseAuth.mockReturnValue({ user: { plan: "free" }, isHydrated: true });
    render(
      <PremiumGate fallback={<span>custom upsell</span>}>
        <span>premium content</span>
      </PremiumGate>,
    );
    expect(screen.getByText("custom upsell")).toBeInTheDocument();
    expect(screen.queryByText("premium content")).toBeNull();
  });
});
