import { describe, it, expect } from "vitest";
import { isAdmin, isProfessor, isTA, isInstructor } from "./roles";

describe("roles", () => {
  it("isAdmin allows admin and super_admin only", () => {
    expect(isAdmin("admin")).toBe(true);
    expect(isAdmin("super_admin")).toBe(true);
    expect(isAdmin("professor")).toBe(false);
    expect(isAdmin("ta")).toBe(false);
    expect(isAdmin("user")).toBe(false);
    expect(isAdmin(undefined)).toBe(false);
    expect(isAdmin(null)).toBe(false);
  });

  it("isProfessor allows professor plus admins", () => {
    expect(isProfessor("professor")).toBe(true);
    expect(isProfessor("admin")).toBe(true);
    expect(isProfessor("super_admin")).toBe(true);
    expect(isProfessor("ta")).toBe(false);
    expect(isProfessor("user")).toBe(false);
    expect(isProfessor(undefined)).toBe(false);
  });

  it("isTA allows ta plus admins (demonstrator surface)", () => {
    expect(isTA("ta")).toBe(true);
    expect(isTA("admin")).toBe(true);
    expect(isTA("super_admin")).toBe(true);
    expect(isTA("professor")).toBe(false);
    expect(isTA("user")).toBe(false);
    expect(isTA(undefined)).toBe(false);
  });

  it("isInstructor allows professor/ta/admins, denies students and anonymous", () => {
    expect(isInstructor("professor")).toBe(true);
    expect(isInstructor("ta")).toBe(true);
    expect(isInstructor("admin")).toBe(true);
    expect(isInstructor("super_admin")).toBe(true);
    expect(isInstructor("user")).toBe(false);
    expect(isInstructor(undefined)).toBe(false);
    expect(isInstructor(null)).toBe(false);
  });
});
