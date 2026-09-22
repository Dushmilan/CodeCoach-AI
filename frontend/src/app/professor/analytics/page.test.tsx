import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectBentoStats,
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";
import ProfessorAnalyticsPage from "./page";

vi.mock("next/link", () => ({
  default: ({ children, ...props }: Record<string, unknown>) => (
    <a {...props}>{children as React.ReactNode}</a>
  ),
}));

describe("ProfessorAnalyticsPage (Issue #176)", () => {
  it("renders owned classroom analytics from the live API", async () => {
    render(<ProfessorAnalyticsPage />);
    expect(
      await screen.findByText(/class analytics/i),
    ).toBeInTheDocument();
    expect(await screen.findByText(/CS101 · Section A/)).toBeInTheDocument();
  });

  it("shows an empty-state with a classrooms link when the professor owns no rooms", async () => {
    server.use(http.get("/api/instructor/classrooms-analytics", () => HttpResponse.json([])));
    render(<ProfessorAnalyticsPage />);
    expect(
      await screen.findByText(/no classrooms yet/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /view classrooms/i }),
    ).toHaveAttribute("href", "/professor/classrooms");
  });

  it("lays classroom stats out as a varied bento and passes taste gates", async () => {
    const { container } = render(<ProfessorAnalyticsPage />);
    await screen.findByText(/CS101 · Section A/);
    expectBentoStats(container);
    expectNoDash(container, "professor analytics");
    expectEyebrowBudget(container, "professor analytics");
    expectNoDuplicateCtas(container, "professor analytics");
  });
});
