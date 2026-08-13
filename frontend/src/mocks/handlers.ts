import { http, HttpResponse } from "msw";

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
    });
  }),
  http.post("/api/auth/register", () => {
    return HttpResponse.json({
      access_token: "test-token",
      expires_in: 86400,
      user: { id: "1", username: "newuser", email: "new@test.com" },
    });
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
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }
    return HttpResponse.json([]);
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
];
