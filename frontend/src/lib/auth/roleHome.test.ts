import { describe, expect, it } from "vitest";
import { roleHomePath, signInPathFor } from "@/lib/auth/roleHome";

describe("roleHome routing conventions (Issue #180)", () => {
  it("maps each role to its home", () => {
    expect(roleHomePath("admin")).toBe("/admin/dashboard");
    expect(roleHomePath("super_admin")).toBe("/admin/dashboard");
    expect(roleHomePath("professor")).toBe("/professor");
    expect(roleHomePath("ta")).toBe("/demonstrator");
    expect(roleHomePath("user")).toBe("/login");
    expect(roleHomePath(null)).toBe("/login");
    expect(roleHomePath(undefined)).toBe("/login");
  });

  it("maps guarded paths to sign-in", () => {
    expect(signInPathFor("/admin/users")).toBe("/admin/login");
    expect(signInPathFor("/admin")).toBe("/admin/login");
    expect(signInPathFor("/professor/analytics")).toBe("/login");
    expect(signInPathFor("/login")).toBe("/login");
    expect(signInPathFor(null)).toBe("/login");
  });
});
