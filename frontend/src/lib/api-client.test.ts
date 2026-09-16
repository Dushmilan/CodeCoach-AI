import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, type AdminHierarchy } from "./api-client";

function mockFetchJson(payload: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: vi.fn().mockResolvedValue(payload),
    text: vi.fn().mockResolvedValue(""),
  } as unknown as Response);
}

describe("apiClient.getAdminHierarchy", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetchJson({ professors: [] }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetches GET /api/admin/hierarchy and parses professors[].courses[].classrooms[]", async () => {
    const payload: AdminHierarchy = {
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
      ],
    };
    const fetchMock = mockFetchJson(payload);
    vi.stubGlobal("fetch", fetchMock);

    const hierarchy = await apiClient.getAdminHierarchy();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/hierarchy",
      expect.objectContaining({ method: "GET" }),
    );
    expect(hierarchy.professors).toHaveLength(1);
    expect(hierarchy.professors[0].username).toBe("professor.ada");
    expect(hierarchy.professors[0].courses[0].title).toBe(
      "Python Fundamentals",
    );
    expect(hierarchy.professors[0].classrooms[0].invite_code).toBe(
      "CS101-A-2026",
    );
    expect(hierarchy.professors[0].classrooms[0].tas).toEqual(["ta-turing"]);
  });

  it("parses an empty roster without inventing rows", async () => {
    vi.stubGlobal("fetch", mockFetchJson({ professors: [] }));
    const hierarchy = await apiClient.getAdminHierarchy();
    expect(hierarchy.professors).toEqual([]);
  });
});

describe("apiClient.getClassroomDetail", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      mockFetchJson({ classroom: null, analytics: null }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetches GET /api/instructor/classrooms/{id} and parses room + analytics", async () => {
    const payload = {
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
    const fetchMock = mockFetchJson(payload);
    vi.stubGlobal("fetch", fetchMock);

    const detail = await apiClient.getClassroomDetail("room-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/instructor/classrooms/room-1",
      expect.objectContaining({ method: "GET" }),
    );
    expect(detail.classroom.id).toBe("room-1");
    expect(detail.classroom.invite_code).toBe("CS101-A-2026");
    expect(detail.analytics.total_students).toBe(1);
    expect(detail.analytics.students[0].user_id).toBe("s1");
  });

  it("encodes classroom ids in the request path", async () => {
    const fetchMock = mockFetchJson({
      classroom: {
        id: "room a/b",
        course_id: "py",
        owner_id: "prof-ada-01",
        name: "Room",
        invite_code: "X",
        term: null,
        schedule: null,
      },
      analytics: {
        total_students: 0,
        avg_completion: 0,
        avg_solved: 0,
        students: [],
      },
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiClient.getClassroomDetail("room a/b");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/instructor/classrooms/room%20a%2Fb",
      expect.objectContaining({ method: "GET" }),
    );
  });
});
