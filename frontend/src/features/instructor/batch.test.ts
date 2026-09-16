import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  getClassroomsAnalytics,
  getClassroomDetail,
} from "./demo";

const ROOMS = [
  {
    id: "live-room-1",
    course_id: "python-fundamentals",
    owner_id: "prof-ada-01",
    name: "Live CS101",
    invite_code: "LIVE-2026",
    term: "Fall 2026",
    schedule: "Mon/Wed 10:00",
  },
  {
    id: "live-room-2",
    course_id: "python-fundamentals",
    owner_id: "prof-ada-01",
    name: "Live CS102",
    invite_code: "LIVE-2027",
    term: "Fall 2026",
    schedule: "Tue/Thu 10:00",
  },
];

function analyticsFor(id: string) {
  return {
    total_students: 1,
    avg_completion: 50.0,
    avg_solved: 2.0,
    students: [
      {
        user_id: `stu-${id}`,
        completed_lessons: 5,
        completion_pct: 50.0,
        attempted: 4,
        solved: 2,
      },
    ],
  };
}

describe("issue #179 batched classroom analytics", () => {
  it("getClassroomsAnalytics resolves N rooms in 1 request", async () => {
    let hits = 0;
    server.use(
      http.get("/api/instructor/classrooms-analytics", () => {
        hits += 1;
        return HttpResponse.json(
          ROOMS.map((classroom) => ({
            classroom,
            analytics: analyticsFor(classroom.id),
          })),
        );
      }),
    );
    const out = await getClassroomsAnalytics();
    expect(hits).toBe(1);
    expect(Object.keys(out.analyticsById).sort()).toEqual([
      "live-room-1",
      "live-room-2",
    ]);
    expect(out.analyticsById["live-room-1"].totalStudents).toBe(1);
    expect(out.analyticsById["live-room-1"].students[0].userId).toBe(
      "stu-live-room-1",
    );
    // Figures identical to the per-room payload shape.
    expect(out.analyticsById["live-room-2"].avgCompletion).toBe(50);
  });

  it("getClassroomDetail resolves room + analytics in 1 request", async () => {
    let hits = 0;
    server.use(
      http.get("/api/instructor/classrooms/:id", () => {
        hits += 1;
        return HttpResponse.json({
          classroom: ROOMS[0],
          analytics: analyticsFor(ROOMS[0].id),
        });
      }),
    );
    const detail = await getClassroomDetail("live-room-1");
    expect(hits).toBe(1);
    expect(detail?.classroom.id).toBe("live-room-1");
    expect(detail?.analytics.totalStudents).toBe(1);
  });

  it("batch never serves demo data on 403 — returns empty instead", async () => {
    server.use(
      http.get("/api/instructor/classrooms-analytics", () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );
    const out = await getClassroomsAnalytics();
    expect(out.rooms).toEqual([]);
    expect(out.analyticsById).toEqual({});
  });
});
