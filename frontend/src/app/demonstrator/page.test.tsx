import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  expectBentoStats,
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";
import DemonstratorOverviewPage from "./page";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "ta-alex-01", username: "demonstrator.turing", role: "ta" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));
vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

describe("DemonstratorOverviewPage", () => {
  it("renders demonstrator overview with assigned classrooms", async () => {
    render(<DemonstratorOverviewPage />);
    expect(
      await screen.findByText(/demonstrator dashboard/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("ta-classrooms")).toBeInTheDocument();
  });

  it("is read-only: no roster management controls", async () => {
    render(<DemonstratorOverviewPage />);
    await screen.findByText(/demonstrator dashboard/i);
    expect(screen.queryByText(/manage roster/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /class analytics/i }),
    ).toBeInTheDocument();
  });

  it("lays stats out as a varied bento and passes taste gates", async () => {
    const { container } = render(<DemonstratorOverviewPage />);
    await screen.findByText(/demonstrator dashboard/i);
    expect(container.querySelectorAll("[data-stat]")).toHaveLength(2);
    expectBentoStats(container);
    expectNoDash(container, "demonstrator overview");
    expectEyebrowBudget(container, "demonstrator overview");
    expectNoDuplicateCtas(container, "demonstrator overview");
  });
});
