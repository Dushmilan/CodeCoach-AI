import { render, screen, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import ProfessorCurriculumPage from "./page";
import { server } from "@/mocks/server";

describe("professor curriculum page", () => {
  it("sends the full CourseCreate payload: slug id, next order, language (issue #296)", async () => {
    let captured: unknown;
    server.use(
      http.get("/api/professor/courses/tree", () =>
        HttpResponse.json({
          courses: [
            { id: "audit-294", title: "Audit Course 294", owner_id: "prof-1", order: 3 },
          ],
          modules: [],
          lessons: [],
        }),
      ),
      http.post("/api/professor/courses", async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json(
          { id: "intro-to-python", title: "Intro to Python", owner_id: "prof-1", order: 4 },
          { status: 201 },
        );
      }),
    );
    render(<ProfessorCurriculumPage />);
    expect(await screen.findByText("Audit Course 294")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/new course title/i), {
      target: { value: "Intro to Python" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create course/i }));
    expect(await screen.findByText("Intro to Python")).toBeInTheDocument();
    expect(captured).toEqual({
      id: "intro-to-python",
      title: "Intro to Python",
      description: "",
      language: "python",
      order: 4,
    });
  });

  it("falls back to order 1 on an empty course list", async () => {
    let captured: { order?: number } | undefined;
    server.use(
      http.get("/api/professor/courses/tree", () =>
        HttpResponse.json({ courses: [], modules: [], lessons: [] }),
      ),
      http.post("/api/professor/courses", async ({ request }) => {
        captured = (await request.json()) as { order?: number };
        return HttpResponse.json(
          { id: "first-course", title: "First course", owner_id: "prof-1", order: 1 },
          { status: 201 },
        );
      }),
    );
    render(<ProfessorCurriculumPage />);
    fireEvent.change(screen.getByLabelText(/new course title/i), {
      target: { value: "First course" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create course/i }));
    expect(await screen.findByText("First course")).toBeInTheDocument();
    expect(captured?.order).toBe(1);
  });

  it("renders owned courses without any /admin links", async () => {
    server.use(
      http.get("/api/professor/courses/tree", () =>
        HttpResponse.json({
          courses: [{ id: "c1", title: "Owned 101", owner_id: "prof-1" }],
          modules: [],
          lessons: [],
        }),
      ),
    );
    render(<ProfessorCurriculumPage />);
    expect(await screen.findByText("Owned 101")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /curriculum/i })).toBeNull();
    document.querySelectorAll("a[href]").forEach((a) => {
      expect(a.getAttribute("href")?.startsWith("/admin")).toBe(false);
    });
  });

  it("renders server detail when course creation fails", async () => {
    server.use(
      http.post("/api/professor/courses", () =>
        HttpResponse.json({ detail: "Course title taken" }, { status: 409 }),
      ),
    );
    render(<ProfessorCurriculumPage />);
    fireEvent.change(screen.getByLabelText(/new course title/i), {
      target: { value: "Dup" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create course/i }));
    expect(await screen.findByText("Course title taken")).toBeInTheDocument();
  });

  it("renders server detail when course rename fails", async () => {
    server.use(
      http.get("/api/professor/courses/tree", () =>
        HttpResponse.json({
          courses: [{ id: "c1", title: "Owned 101", owner_id: "prof-1" }],
          modules: [],
          lessons: [],
        }),
      ),
      http.put("/api/professor/courses/c1", () =>
        HttpResponse.json(
          { detail: "ANIMATION gate blocked publish" },
          { status: 422 },
        ),
      ),
    );
    render(<ProfessorCurriculumPage />);
    expect(await screen.findByText("Owned 101")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    fireEvent.change(screen.getByLabelText(/edit course title/i), {
      target: { value: "Renamed" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(
      await screen.findByText("ANIMATION gate blocked publish"),
    ).toBeInTheDocument();
  });
});
