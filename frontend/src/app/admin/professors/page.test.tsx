import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";
import ProfessorsPage from "./page";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "admin-1", username: "admin", role: "admin" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

const hierarchyPayload = {
  professors: [
    {
      id: "prof-ada-01",
      username: "professor.ada",
      courses: [{ id: "py", title: "Python Fundamentals", lessons: 12 }],
      classrooms: [
        {
          id: "room-1",
          name: "CS101 · Section A",
          invite_code: "CS101-A-2026",
          tas: ["ta-turing"],
          students: 5,
          avg_completion: 42.5,
        },
      ],
    },
    {
      id: "prof-grace-02",
      username: "professor.grace",
      courses: [
        { id: "ds", title: "Data Structures", lessons: 8 },
        { id: "algo", title: "Algorithms", lessons: 6 },
      ],
      classrooms: [],
    },
  ],
};

describe("Admin Professors roster page", () => {
  it("renders one row per professor with counts and drill-down links", async () => {
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorsPage />);

    expect(await screen.findByText("professor.ada")).toBeInTheDocument();
    expect(screen.getByText("professor.grace")).toBeInTheDocument();

    // Counts per professor (courses + classrooms + students).
    expect(screen.getByText(/1 courses.*1 classrooms.*5 students/)).toBeInTheDocument();
    expect(screen.getByText(/2 courses.*0 classrooms.*0 students/)).toBeInTheDocument();

    const adaLink = screen.getByTestId("professor-link-prof-ada-01");
    expect(adaLink).toHaveAttribute("href", "/admin/professors/prof-ada-01");
    expect(screen.getByTestId("professor-link-prof-grace-02")).toHaveAttribute(
      "href",
      "/admin/professors/prof-grace-02",
    );
  });

  it("scopes the roster to the hierarchy payload (no invented rows)", async () => {
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorsPage />);
    await screen.findByText("professor.ada");
    expect(screen.queryByText("professor.unknown")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getAllByTestId(/^professor-link-/)).toHaveLength(2),
    );
  });

  it("shows an empty state when no professors exist", async () => {
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json({ professors: [] }),
      ),
    );
    render(<ProfessorsPage />);
    expect(await screen.findByText(/no professors/i)).toBeInTheDocument();
  });

  it("renders avatar chips plus taste gates for each professor card", async () => {
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    const { container } = render(<ProfessorsPage />);

    expect(await screen.findByText("professor.ada")).toBeInTheDocument();
    expect(screen.getAllByTestId("professor-avatar")).toHaveLength(2);
    expectNoDash(container, "admin professors");
    expectEyebrowBudget(container, "admin professors");
    expectNoDuplicateCtas(container, "admin professors");
  });
});
