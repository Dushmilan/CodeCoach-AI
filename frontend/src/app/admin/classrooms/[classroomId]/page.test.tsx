import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import AdminClassroomDetailPage from "./page";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "admin-1", username: "admin", role: "admin" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

const mockId = vi.hoisted(() => ({ current: "room-1" }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ classroomId: mockId.current }),
}));

const detailPayload = {
  classroom: {
    id: "room-1",
    course_id: "py",
    owner_id: "prof-ada-01",
    name: "CS101 · Section A",
    invite_code: "CS101-A-2026",
    term: "Fall 2026",
    schedule: "Mon/Wed 10:00",
  },
  analytics: {
    total_students: 1,
    avg_completion: 60.0,
    avg_solved: 1.0,
    students: [
      {
        user_id: "s1",
        completed_lessons: 6,
        completion_pct: 60.0,
        attempted: 2,
        solved: 1,
      },
    ],
  },
};

describe("Admin classroom detail page", () => {
  it("renders the room plus analytics from the instructor detail endpoint", async () => {
    mockId.current = "room-1";
    server.use(
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json(detailPayload),
      ),
    );
    render(<AdminClassroomDetailPage />);

    expect(await screen.findByText("CS101 · Section A")).toBeInTheDocument();
    expect(screen.getByText("CS101-A-2026")).toBeInTheDocument();
    expect(screen.getByTestId("classroom-students")).toHaveTextContent("1");
    expect(screen.getByTestId("classroom-avg-completion")).toHaveTextContent(
      "60",
    );
    expect(await screen.findByText("s1")).toBeInTheDocument();
  });

  it("exposes an analytics section for the professor-page anchor link", async () => {
    mockId.current = "room-1";
    server.use(
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json(detailPayload),
      ),
    );
    render(<AdminClassroomDetailPage />);

    await screen.findByText("CS101 · Section A");
    expect(screen.getByTestId("classroom-analytics")).toBeInTheDocument();
  });

  it("shows an empty state when the classroom is unknown", async () => {
    mockId.current = "room-unknown";
    server.use(
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({ detail: "Classroom not found" }, { status: 404 }),
      ),
    );
    render(<AdminClassroomDetailPage />);

    expect(await screen.findByText(/classroom not found/i)).toBeInTheDocument();
  });
});
