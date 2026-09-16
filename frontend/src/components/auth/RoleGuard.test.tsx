import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { RoleGuard } from "./RoleGuard";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  push: vi.fn(),
  authState: {
    user: null as { role?: string } | null,
    isAuthenticated: false,
    isHydrated: true,
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace, push: mocks.push }),
}));

vi.mock("@/providers", () => ({
  useAuth: () => mocks.authState,
}));

describe("RoleGuard", () => {
  beforeEach(() => {
    mocks.replace.mockReset();
    mocks.push.mockReset();
    mocks.authState = {
      user: null,
      isAuthenticated: false,
      isHydrated: true,
    };
  });

  it("shows a spinner while auth is hydrating", () => {
    mocks.authState = {
      user: null,
      isAuthenticated: false,
      isHydrated: false,
    };
    const { container } = render(
      <RoleGuard allowedRoles={["admin"]} loginHref="/admin/login" deniedMessage="Nope">
        <div>secret</div>
      </RoleGuard>,
    );
    expect(container.querySelector(".animate-spin")).not.toBeNull();
    expect(screen.queryByText("secret")).toBeNull();
  });

  it("redirects unauthenticated users to the sign-in page", async () => {
    mocks.authState = {
      user: null,
      isAuthenticated: false,
      isHydrated: true,
    };
    render(
      <RoleGuard allowedRoles={["admin"]} loginHref="/admin/login" deniedMessage="Nope">
        <div>secret</div>
      </RoleGuard>,
    );
    await waitFor(() => {
      expect(mocks.replace).toHaveBeenCalledWith("/admin/login");
    });
    expect(screen.queryByText("secret")).toBeNull();
  });

  it("shows Access Denied with a home link for the wrong role", () => {
    mocks.authState = {
      user: { role: "student" },
      isAuthenticated: true,
      isHydrated: true,
    };
    render(
      <RoleGuard
        allowedRoles={["admin"]}
        loginHref="/admin/login"
        deniedMessage="You need admin privileges to access this area."
      >
        <div>secret</div>
      </RoleGuard>,
    );
    expect(screen.getByText("Access Denied")).toBeDefined();
    expect(
      screen.getByText("You need admin privileges to access this area."),
    ).toBeDefined();
    const homeLink = screen.getByRole("link", { name: /home/i });
    expect(homeLink.getAttribute("href")).toBe("/");
    expect(screen.queryByText("secret")).toBeNull();
    expect(mocks.replace).not.toHaveBeenCalled();
  });

  it("renders children for an allowed role", () => {
    mocks.authState = {
      user: { role: "admin" },
      isAuthenticated: true,
      isHydrated: true,
    };
    render(
      <RoleGuard allowedRoles={["admin"]} loginHref="/admin/login" deniedMessage="Nope">
        <div>secret</div>
      </RoleGuard>,
    );
    expect(screen.getByText("secret")).toBeDefined();
    expect(mocks.replace).not.toHaveBeenCalled();
  });

  it("denied panel offers home and sign-in links (no open redirect)", () => {
    mocks.authState = {
      user: { role: "student" },
      isAuthenticated: true,
      isHydrated: true,
    };
    render(
      <RoleGuard
        allowedRoles={["admin"]}
        loginHref="/admin/login"
        deniedMessage="You need admin privileges to access this area."
      >
        <div>secret</div>
      </RoleGuard>,
    );
    const homeLink = screen.getByRole("link", { name: /home/i });
    expect(homeLink.getAttribute("href")).toBe("/");
    const signInLink = screen.getByRole("link", { name: /sign.?in/i });
    expect(signInLink.getAttribute("href")).toBe("/admin/login");
  });

  it("redirects with router.replace (not push)", async () => {
    mocks.authState = {
      user: null,
      isAuthenticated: false,
      isHydrated: true,
    };
    render(
      <RoleGuard allowedRoles={["admin"]} loginHref="/admin/login" deniedMessage="Nope">
        <div>secret</div>
      </RoleGuard>,
    );
    await waitFor(() => {
      expect(mocks.replace).toHaveBeenCalledWith("/admin/login");
    });
    expect(mocks.push).not.toHaveBeenCalled();
  });
});
