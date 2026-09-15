import { describe, it, expect } from "vitest";
import {
  getClassAnalytics,
  getClassroom,
  canManageRoster,
  canEditCourses,
  canViewAnalytics,
} from "./demo";

describe("instructor demo dataset", () => {
  it("aggregates class analytics for CS101-A", () => {
    const a = getClassAnalytics("class-cs101-a");
    expect(a.totalStudents).toBe(5);
    expect(a.avgCompletion).toBeGreaterThanOrEqual(0);
    expect(a.avgCompletion).toBeLessThanOrEqual(100);
    expect(a.students).toHaveLength(5);
    expect(a.atRisk.length).toBeGreaterThanOrEqual(1);
  });

  it("resolves classrooms with course linkage", () => {
    const c = getClassroom("class-cs101-a");
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
