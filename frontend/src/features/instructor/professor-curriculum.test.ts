import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import { getProfessorCourseTree, getProfessorCourses } from "./demo";

const LIVE_TREE = {
  courses: [
    {
      id: "prof-course-1",
      title: "Prof Course",
      description: "owned",
      language: "python",
      icon: "code",
      order: 1,
      owner_id: "prof-ada-01",
    },
  ],
  modules: [],
  lessons: [],
};

function useLiveTree() {
  server.use(
    http.get("/api/professor/courses/tree", () => HttpResponse.json(LIVE_TREE)),
  );
}

function useOfflineTree() {
  server.use(
    http.get("/api/professor/courses/tree", () => HttpResponse.error()),
  );
}

describe("professor curriculum live-first (Issue #185)", () => {
  it("getProfessorCourseTree returns the live owned tree", async () => {
    useLiveTree();
    const tree = await getProfessorCourseTree();
    expect(tree.courses).toHaveLength(1);
    expect(tree.courses[0]).toMatchObject({
      id: "prof-course-1",
      owner_id: "prof-ada-01",
    });
  });

  it("getProfessorCourses returns live courses", async () => {
    useLiveTree();
    const courses = await getProfessorCourses();
    expect(courses.map((c) => c.id)).toEqual(["prof-course-1"]);
  });

  it("falls back to demo courses when the API is unreachable", async () => {
    useOfflineTree();
    const courses = await getProfessorCourses();
    expect(courses.map((c) => c.id).sort()).toEqual([
      "data-structures",
      "python-fundamentals",
    ]);
  });

  it("never serves demo data on 403 — returns empty instead", async () => {
    server.use(
      http.get("/api/professor/courses/tree", () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );
    await expect(getProfessorCourseTree()).resolves.toEqual({
      courses: [],
      modules: [],
      lessons: [],
    });
    await expect(getProfessorCourses()).resolves.toEqual([]);
  });
});
