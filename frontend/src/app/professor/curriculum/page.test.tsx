import { render, screen, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import ProfessorCurriculumPage from "./page";
import { server } from "@/mocks/server";

describe("professor curriculum page", () => {
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
