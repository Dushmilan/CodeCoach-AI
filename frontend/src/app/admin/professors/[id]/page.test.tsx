import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import ProfessorDetailPage from "./page";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "admin-1", username: "admin", role: "admin" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

const mockId = vi.hoisted(() => ({ current: "prof-ada-01" }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: mockId.current }),
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

describe("Admin professor detail page", () => {
  it("resolves the professor from the hierarchy payload", async () => {
    mockId.current = "prof-ada-01";
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorDetailPage />);

    expect(await screen.findByText("professor.ada")).toBeInTheDocument();
    expect(screen.getByText("Python Fundamentals")).toBeInTheDocument();
    expect(screen.queryByText("professor.grace")).not.toBeInTheDocument();
  });

  it("links each classroom to its detail page plus its analytics section", async () => {
    mockId.current = "prof-ada-01";
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorDetailPage />);

    await screen.findByText("CS101 · Section A");
    expect(screen.getByTestId("classroom-link-room-1")).toHaveAttribute(
      "href",
      "/admin/classrooms/room-1",
    );
    expect(
      screen.getByTestId("classroom-analytics-link-room-1"),
    ).toHaveAttribute("href", "/admin/classrooms/room-1#analytics");
  });

  it("shows an empty state when the professor id is unknown", async () => {
    mockId.current = "prof-unknown";
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorDetailPage />);

    expect(await screen.findByText(/professor not found/i)).toBeInTheDocument();
  });

  it("shows an empty classrooms state when the professor has no rooms", async () => {
    mockId.current = "prof-grace-02";
    server.use(
      http.get("/api/admin/hierarchy", () =>
        HttpResponse.json(hierarchyPayload),
      ),
    );
    render(<ProfessorDetailPage />);

    await screen.findByText("professor.grace");
    expect(screen.getByText(/no classrooms/i)).toBeInTheDocument();
  });
});
