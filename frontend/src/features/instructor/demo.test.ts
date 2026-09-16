import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  getClassAnalytics,
  getClassroom,
  getClassrooms,
  canManageRoster,
  canEditCourses,
  canViewAnalytics,
} from "./demo";

const LIVE_ROOM = {
  id: "live-room-1",
  course_id: "python-fundamentals",
  owner_id: "prof-ada-01",
  name: "Live CS101",
  invite_code: "LIVE-2026",
  term: "Fall 2026",
  schedule: "Mon/Wed 10:00",
};

const LIVE_DETAIL = {
  classroom: LIVE_ROOM,
  analytics: {
    total_students: 2,
    avg_completion: 55.5,
    avg_solved: 7.5,
    students: [
      {
        user_id: "stu-live-01",
        completed_lessons: 20,
        completion_pct: 80.0,
        attempted: 20,
        solved: 12,
      },
      {
        user_id: "stu-live-02",
        completed_lessons: 5,
        completion_pct: 10.0,
        attempted: 15,
        solved: 3,
      },
    ],
  },
};

function useLiveClassrooms() {
  server.use(
    http.get("/api/instructor/classrooms", () => HttpResponse.json([LIVE_ROOM])),
    http.get("/api/instructor/classrooms/:id", () =>
      HttpResponse.json(LIVE_DETAIL),
    ),
  );
}

function useOfflineClassrooms() {
  server.use(
    http.get("/api/instructor/classrooms", () => HttpResponse.error()),
    http.get("/api/instructor/classrooms/:id", () => HttpResponse.error()),
  );
}

describe("instructor demo dataset", () => {
  it("aggregates class analytics for CS101-A", async () => {
    useOfflineClassrooms();
    const a = await getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBe(5);
    expect(a.avgCompletion).toBeGreaterThanOrEqual(0);
    expect(a.avgCompletion).toBeLessThanOrEqual(100);
    expect(a.students).toHaveLength(5);
    expect(a.atRisk.length).toBeGreaterThanOrEqual(1);
  });

  it("resolves classrooms with course linkage", async () => {
    useOfflineClassrooms();
    const c = await getClassroom("class-cs101-a");
    expect(c?.courseId).toBe("python-fundamentals");
    expect(c?.inviteCode).toBeTruthy();
  });

  it("enforces the TA permission matrix", () => {
    expect(canManageRoster("professor")).toBe(true);
    expect(canManageRoster("ta")).toBe(false);
    expect(canEditCourses("professor")).toBe(true);
    expect(canEditCourses("ta")).toBe(false);
    expect(canViewAnalytics("professor")).toBe(true);
    expect(canViewAnalytics("ta")).toBe(true);
    expect(canViewAnalytics("user")).toBe(false);
  });
});

describe("instructor live API (Issue #159)", () => {
  it("getClassrooms returns live rooms mapped to the page contract", async () => {
    useLiveClassrooms();
    const rooms = await getClassrooms();
    expect(rooms).toHaveLength(1);
    expect(rooms[0]).toMatchObject({
      id: "live-room-1",
      name: "Live CS101",
      courseId: "python-fundamentals",
      ownerId: "prof-ada-01",
      inviteCode: "LIVE-2026",
    });
  });

  it("getClassroom returns the live room", async () => {
    useLiveClassrooms();
    const room = await getClassroom("live-room-1");
    expect(room?.name).toBe("Live CS101");
    expect(room?.inviteCode).toBe("LIVE-2026");
  });

  it("getClassroom returns null for an unknown room", async () => {
    server.use(
      http.get("/api/instructor/classrooms", () => HttpResponse.json([])),
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({ detail: "Classroom not found" }, { status: 404 }),
      ),
    );
    expect(await getClassroom("no-such-room")).toBeNull();
  });

  it("getClassAnalytics returns live aggregates with mapped students", async () => {
    useLiveClassrooms();
    const a = await getClassAnalytics("live-room-1");
    expect(a.totalStudents).toBe(2);
    expect(a.avgCompletion).toBe(55.5);
    expect(a.avgSolved).toBe(7.5);
    expect(a.students).toHaveLength(2);
    expect(a.students[0]).toMatchObject({
      userId: "stu-live-01",
      completionPct: 80,
      solved: 12,
      attempted: 20,
    });
    // Completion < 35% flags the second live student as at risk.
    expect(a.atRisk.map((s) => s.userId)).toEqual(["stu-live-02"]);
  });

  it("maps live usernames onto roster rows (Issue #177)", async () => {
    server.use(
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({
          classroom: LIVE_ROOM,
          analytics: {
            total_students: 2,
            avg_completion: 55.5,
            avg_solved: 7.5,
            students: [
              {
                user_id: "stu-live-01",
                username: "mia.live",
                completed_lessons: 20,
                completion_pct: 80.0,
                attempted: 20,
                solved: 12,
              },
              {
                user_id: "stu-live-02",
                completed_lessons: 5,
                completion_pct: 10.0,
                attempted: 15,
                solved: 3,
              },
            ],
          },
        }),
      ),
    );
    const a = await getClassAnalytics("live-room-1");
    expect(a.students[0]).toMatchObject({
      userId: "stu-live-01",
      username: "mia.live",
      name: "mia.live",
    });
    // Missing username falls back to the user id so the roster keeps shape.
    expect(a.students[1]).toMatchObject({
      userId: "stu-live-02",
      username: "stu-live-02",
    });
  });

  it("falls back to the demo dataset when the API is unreachable", async () => {
    useOfflineClassrooms();
    const rooms = await getClassrooms();
    expect(rooms.map((r) => r.id).sort()).toEqual([
      "class-cs101-a",
      "class-cs201-b",
    ]);
    const a = await getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBe(5);
    expect(a.skillMastery.length).toBeGreaterThan(0);
  });

  it("falls back to the demo dataset on a 500", async () => {
    server.use(
      http.get("/api/instructor/classrooms", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const rooms = await getClassrooms();
    expect(rooms.map((r) => r.id).sort()).toEqual([
      "class-cs101-a",
      "class-cs201-b",
    ]);
  });

  it("never serves demo data on 403 — returns empty instead", async () => {
    server.use(
      http.get("/api/instructor/classrooms", () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );
    await expect(getClassrooms()).resolves.toEqual([]);
    await expect(getClassroom("class-cs101-a")).resolves.toBeNull();
    const a = await getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBe(0);
    expect(a.students).toEqual([]);
    expect(a.skillMastery).toEqual([]);
  });

  it("never serves demo data on 401 — returns empty instead", async () => {
    server.use(
      http.get("/api/instructor/classrooms", () =>
        HttpResponse.json({ detail: "Not authenticated" }, { status: 401 }),
      ),
      http.get("/api/instructor/classrooms/:id", () =>
        HttpResponse.json({ detail: "Not authenticated" }, { status: 401 }),
      ),
    );
    await expect(getClassrooms()).resolves.toEqual([]);
    await expect(getClassroom("class-cs101-a")).resolves.toBeNull();
    const a = await getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBe(0);
    expect(a.students).toEqual([]);
  });
});
