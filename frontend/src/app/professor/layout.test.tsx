import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

const roleGuardCalls: Array<{
  allowedRoles: string[];
  loginHref: string;
  deniedMessage: string;
}> = [];

vi.mock("@/components/auth/RoleGuard", () => ({
  RoleGuard: (props: {
    allowedRoles: string[];
    loginHref: string;
    deniedMessage: string;
    children: React.ReactNode;
  }) => {
    roleGuardCalls.push({
      allowedRoles: props.allowedRoles,
      loginHref: props.loginHref,
      deniedMessage: props.deniedMessage,
    });
    return <div data-testid="roleguard">{props.children}</div>;
  },
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/professor",
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { role: "professor" },
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

vi.mock("@/components/instructor/InstructorSidebar", () => ({
  InstructorSidebar: ({ base }: { base: string }) => (
    <div data-testid="sidebar" data-base={base} />
  ),
}));

import ProfessorLayout from "./layout";

describe("ProfessorLayout", () => {
  beforeEach(() => {
    roleGuardCalls.length = 0;
  });

  it("guards the professor area with RoleGuard (professor/admin/super_admin, /login)", () => {
    render(
      <ProfessorLayout>
        <div>prof-child</div>
      </ProfessorLayout>,
    );
    expect(roleGuardCalls).toHaveLength(1);
    expect(roleGuardCalls[0].allowedRoles).toEqual([
      "professor",
      "admin",
      "super_admin",
    ]);
    expect(roleGuardCalls[0].loginHref).toBe("/login");
    expect(roleGuardCalls[0].deniedMessage).toMatch(/professor/i);
    expect(screen.getByText("prof-child")).toBeDefined();
    expect(screen.getByTestId("roleguard")).toBeDefined();
  });
});
