import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
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
  it("renders professor overview with classrooms and analytics links", async () => {
    render(<ProfessorOverviewPage />);
    expect(
      await screen.findByText(/professor dashboard/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("prof-classrooms")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /class analytics/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /courses/i })).toBeInTheDocument();
  });

  it("shows invite codes for roster management", async () => {
    render(<ProfessorOverviewPage />);
    expect(await screen.findByText(/CS101-A-2026/)).toBeInTheDocument();
  });

  it("reads classrooms from the live API", async () => {
    server.use(
      http.get("/api/instructor/classrooms", () =>
        HttpResponse.json([
          {
            id: "live-room-1",
            course_id: "python-fundamentals",
            owner_id: "prof-ada-01",
            name: "Live CS101",
            invite_code: "LIVE-2026",
            term: "Fall 2026",
            schedule: "Mon/Wed 10:00",
          },
        ]),
      ),
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({
          classroom: {
            id: "live-room-1",
            course_id: "python-fundamentals",
            owner_id: "prof-ada-01",
            name: "Live CS101",
            invite_code: "LIVE-2026",
            term: "Fall 2026",
            schedule: "Mon/Wed 10:00",
          },
          analytics: {
            total_students: 1,
            avg_completion: 50,
            avg_solved: 4,
            students: [
              {
                user_id: "stu-live-01",
                completed_lessons: 18,
                completion_pct: 50,
                attempted: 20,
                solved: 4,
              },
            ],
          },
        }),
      ),
    );
    render(<ProfessorOverviewPage />);
    expect(await screen.findByText("Live CS101")).toBeInTheDocument();
    expect(await screen.findByText(/LIVE-2026/)).toBeInTheDocument();
  });
});
