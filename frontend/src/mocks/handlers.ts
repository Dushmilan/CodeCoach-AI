import { http, HttpResponse } from "msw";
import demoData from "@/data/instructor-demo.json";

// Instructor live endpoints (Issue #159) — default stubs serve the committed
// demo dataset in live shapes so pages render through the fetch path in
// tests/Storybook. Tests override via server.use() for live/failure cases.

export const handlers = [
  http.get("/api/questions/", () => {
    return HttpResponse.json({ questions: [], total: 0 });
  }),
  http.get("/api/questions/stats", () => {
    return HttpResponse.json({ total: 0, by_difficulty: {}, by_category: {} });
  }),
  http.get("/api/questions/categories", () => {
    return HttpResponse.json({ categories: [] });
  }),
  http.get("/api/questions/companies", () => {
    return HttpResponse.json({ companies: [] });
  }),
  http.get("/api/run/languages", () => {
    return HttpResponse.json({ languages: [] });
  }),
  http.post("/api/auth/login", () => {
    return HttpResponse.json({
      access_token: "test-token",
      expires_in: 86400,
      user: { id: "1", username: "testuser", email: "test@test.com" },
      csrf_token: "mocked-csrf-token",
    });
  }),
  http.post("/api/auth/register", () => {
    return HttpResponse.json({
      access_token: "test-token",
      expires_in: 86400,
      user: { id: "1", username: "newuser", email: "new@test.com" },
      csrf_token: "mocked-csrf-token",
    });
  }),
  http.post("/api/auth/refresh", () => {
    return HttpResponse.json({
      access_token: "refreshed-token",
      expires_in: 1800,
      user: { id: "1", username: "testuser", email: "test@test.com" },
      csrf_token: "mocked-csrf-token",
    });
  }),
  http.post("/api/auth/logout", () => {
    return new HttpResponse(null, { status: 204 });
  }),
  http.get("/api/auth/me", () => {
    return HttpResponse.json({
      id: "1",
      username: "testuser",
      email: "test@test.com",
    });
  }),
  http.post("/api/run/", () => {
    return HttpResponse.json({
      stdout: "Hello\n",
      stderr: "",
      exit_code: 0,
      language: "python",
      version: "3.10.0",
    });
  }),
  http.post("/api/coach/", () => {
    return HttpResponse.json({
      response: "Here is a hint...",
      mode: "hint",
      language: "python",
    });
  }),
  http.post("/api/coach/animate", () => {
    return HttpResponse.json({
      animation: {
        type: "linear_search",
        title: "Searching for 4",
        data: { values: [5, 1, 2, 3, 4, 6], target: 4 },
        steps: [
          {
            operation: "compare",
            index: 0,
            value: 5,
            result: "mismatch",
            narration: "5 is not the target, continue searching.",
          },
          {
            operation: "compare",
            index: 4,
            value: 4,
            result: "match",
            narration: "Found the target 4 at index 4.",
          },
        ],
      },
    });
  }),
  http.get("/health", () => {
    return HttpResponse.json({ status: "healthy" });
  }),
  http.get("/api/skills/me/recommended-questions", ({ request }) => {
    const auth = request.headers.get("Authorization");
    if (!auth) {
      return HttpResponse.json(
        { detail: "Not authenticated" },
        { status: 401 },
      );
    }
    return HttpResponse.json([]);
  }),
  http.get("/api/skills/boilerplate", () => {
    return HttpResponse.json({ skills: [], edges: [] });
  }),
  http.get("/api/skills/me/skills", ({ request }) => {
    const auth = request.headers.get("Authorization");
    if (!auth) {
      return HttpResponse.json(
        { detail: "Not authenticated" },
        { status: 401 },
      );
    }
    return HttpResponse.json({ skills: [], edges: [] });
  }),
  http.get("/api/courses/", () => {
    return HttpResponse.json({
      courses: [
        {
          id: "1",
          title: "Test Course",
          description: "A test course",
          module_count: 1,
        },
      ],
    });
  }),
  http.get("/api/courses/:courseId", ({ params }) => {
    return HttpResponse.json({
      id: params.courseId,
      title: "Test Course",
      description: "A test course",
      modules: [],
    });
  }),
  http.get("/api/courses/lessons/:lessonId", ({ params }) => {
    return HttpResponse.json({
      id: params.lessonId,
      title: "Test Lesson",
      description: "A test lesson",
      content: "Lesson content",
      type: "theory",
    });
  }),
  // Instructor demo (Issue #159, phase 2) — serves the committed demo dataset
  // in tests/Storybook. Live mode calls the real /api/instructor/* backend.
  http.get("/api/instructor/classrooms", () => {
    return HttpResponse.json(
      demoData.classrooms.map((c) => ({
        id: c.id,
        course_id: c.courseId,
        owner_id: c.ownerId,
        name: c.name,
        invite_code: c.inviteCode,
        term: c.term,
        schedule: c.schedule,
      })),
    );
  }),
  http.get("/api/instructor/classrooms/:id", ({ params }) => {
    const room = demoData.classrooms.find((c) => c.id === params.id);
    if (!room) {
      return HttpResponse.json(
        { detail: "Classroom not found" },
        { status: 404 },
      );
    }
    const enrolled = demoData.enrollments.filter(
      (e) => e.classroomId === room.id,
    );
    const students = enrolled.map((e) => {
      const p = demoData.progress.find(
        (r) => r.userId === e.userId && r.classroomId === room.id,
      );
      const completed = p?.completedLessons ?? 0;
      return {
        user_id: e.userId,
        completed_lessons: completed,
        completion_pct: Math.round((completed / room.totalLessons) * 100),
        attempted: p?.attempted ?? 0,
        solved: p?.solved ?? 0,
      };
    });
    const total = students.length;
    return HttpResponse.json({
      classroom: {
        id: room.id,
        course_id: room.courseId,
        owner_id: room.ownerId,
        name: room.name,
        invite_code: room.inviteCode,
        term: room.term,
        schedule: room.schedule,
      },
      analytics: {
        total_students: total,
        avg_completion: total
          ? Math.round(
              (students.reduce((s, x) => s + x.completion_pct, 0) / total) * 10,
            ) / 10
          : 0,
        avg_solved: total
          ? Math.round(
              (students.reduce((s, x) => s + x.solved, 0) / total) * 100,
            ) / 100
          : 0,
        students,
      },
    });
  }),
  http.get("/api/instructor/class-analytics", ({ request }) => {
    const url = new URL(request.url);
    const ids = (url.searchParams.get("user_ids") ?? "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return HttpResponse.json({
      total_students: ids.length,
      avg_completion: 0.0,
      avg_solved: 0.0,
      students: [],
    });
  }),
  http.get("/api/professor/courses/tree", () => {
    return HttpResponse.json({ courses: [], modules: [], lessons: [] });
  }),
];
