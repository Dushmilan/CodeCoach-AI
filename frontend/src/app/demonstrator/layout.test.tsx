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
  usePathname: () => "/demonstrator",
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { role: "ta" },
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

import DemonstratorLayout from "./layout";

describe("DemonstratorLayout", () => {
  beforeEach(() => {
    roleGuardCalls.length = 0;
  });

  it("guards the demonstrator area with RoleGuard (ta/professor/admin/super_admin, /login)", () => {
    render(
      <DemonstratorLayout>
        <div>demo-child</div>
      </DemonstratorLayout>,
    );
    expect(roleGuardCalls).toHaveLength(1);
    expect(roleGuardCalls[0].allowedRoles).toEqual([
      "ta",
      "professor",
      "admin",
      "super_admin",
    ]);
    expect(roleGuardCalls[0].loginHref).toBe("/login");
    expect(roleGuardCalls[0].deniedMessage).toMatch(/demonstrator/i);
    expect(screen.getByText("demo-child")).toBeDefined();
    expect(screen.getByTestId("roleguard")).toBeDefined();
  });
});
