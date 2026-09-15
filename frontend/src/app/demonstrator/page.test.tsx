import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
});
