import { render, screen } from "@testing-library/react";
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
});
