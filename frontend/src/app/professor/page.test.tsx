import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ProfessorOverviewPage from "./page";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "prof-ada-01", username: "professor.ada", role: "professor" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));
vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

describe("ProfessorOverviewPage", () => {
  it("renders professor overview with classrooms and analytics links", () => {
    render(<ProfessorOverviewPage />);
    expect(screen.getByText(/professor dashboard/i)).toBeInTheDocument();
    expect(screen.getByTestId("prof-classrooms")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /class analytics/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /courses/i })).toBeInTheDocument();
  });

  it("shows invite codes for roster management", () => {
    render(<ProfessorOverviewPage />);
    expect(screen.getByText(/CS101-A-2026/)).toBeInTheDocument();
  });
});
