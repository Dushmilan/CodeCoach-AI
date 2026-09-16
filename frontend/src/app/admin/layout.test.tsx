"use client";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AdminLayout from "./layout";

const replace = vi.fn();
let authState = { user: null as null | { role: string }, isAuthenticated: false, isHydrated: true };

vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/users",
  useRouter: () => ({ replace, push: vi.fn() }),
}));

vi.mock("@/providers", () => ({
  useAuth: () => ({ ...authState, logout: vi.fn() }),
}));

vi.mock("@/components/admin/AdminSidebar", () => ({
  __esModule: true,
  default: () => <div data-testid="admin-sidebar" />,
}));

vi.mock("@/components/settings/SettingsModal", () => ({
  SettingsModal: () => null,
}));

vi.mock("next-themes", () => ({
  useTheme: () => ({ resolvedTheme: "light", setTheme: vi.fn() }),
}));

describe("admin layout guard conventions (Issue #180)", () => {
  it("redirects unauthenticated users to admin sign-in", () => {
    authState = { user: null, isAuthenticated: false, isHydrated: true };
    render(
      <AdminLayout>
        <div>child</div>
      </AdminLayout>,
    );
    expect(replace).toHaveBeenCalledWith("/admin/login");
  });

  it("denied panel links home and sign-in for wrong roles", () => {
    authState = {
      user: { role: "professor" },
      isAuthenticated: true,
      isHydrated: true,
    };
    render(
      <AdminLayout>
        <div>child</div>
      </AdminLayout>,
    );
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(screen.getByText("Back to home")).toBeInTheDocument();
    expect(screen.getByText("Go to sign-in")).toBeInTheDocument();
  });
});
