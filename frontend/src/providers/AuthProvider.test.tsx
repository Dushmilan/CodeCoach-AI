import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthProvider";
import { authService } from "@/features/auth/auth.service";
import { setAccessToken } from "@/lib/auth-session";

function TestComponent() {
  const { user, token, isAuthenticated, isLoading, login, register, logout } =
    useAuth();
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? "Logged in" : "Logged out"}
      </div>
      {user && <div data-testid="username">{user.username}</div>}
      {token && <div data-testid="token-present">yes</div>}
      <button data-testid="login-btn" onClick={() => login("u", "p")}>
        Login
      </button>
      <button data-testid="register-btn" onClick={() => login("u", "p")}>
        Register
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
}

const userFixture = (username: string) => ({
  id: "1",
  username,
  email: `${username}@t.com`,
  created_at: "2024-01-01",
  is_active: true,
});

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>,
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setAccessToken(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    setAccessToken(null);
  });

  it("shows loading state while restoring session via refresh cookie", () => {
    vi.spyOn(authService, "refresh").mockImplementation(
      () => new Promise(() => {}),
    );
    renderWithProvider();
    expect(screen.getByText("Loading...")).toBeDefined();
  });

  it("shows logged out when no refresh cookie session exists", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No session"));
    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
  });

  it("restores session by exchanging the httpOnly refresh cookie", async () => {
    vi.spyOn(authService, "refresh").mockResolvedValue({
      access_token: "fresh_access",
      token_type: "bearer",
      expires_in: 1800,
      user: userFixture("testuser"),
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
      expect(screen.getByTestId("username").textContent).toBe("testuser");
    });
    // Access token is in memory only — never written to localStorage.
    expect(localStorage.getItem("auth_token")).toBeNull();
  });

  it("login sets user + in-memory token without touching localStorage", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No session"));
    vi.spyOn(authService, "login").mockResolvedValue({
      access_token: "new_jwt",
      token_type: "bearer",
      expires_in: 1800,
      user: userFixture("newuser"),
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });

    await userEvent.click(screen.getByTestId("login-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
      expect(screen.getByTestId("username").textContent).toBe("newuser");
      expect(screen.getByTestId("token-present").textContent).toBe("yes");
    });
    // SEC-2: no token persistence in localStorage.
    expect(localStorage.getItem("auth_token")).toBeNull();
    expect(localStorage.getItem("auth_refresh_token")).toBeNull();
  });

  it("register sets user and does not persist refresh token to localStorage", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No session"));
    vi.spyOn(authService, "login").mockResolvedValue({
      access_token: "reg_jwt",
      token_type: "bearer",
      expires_in: 1800,
      user: userFixture("reguser"),
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });

    await userEvent.click(screen.getByTestId("register-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
    });
    expect(localStorage.getItem("auth_refresh_token")).toBeNull();
  });

  it("logout calls the backend and clears state", async () => {
    vi.spyOn(authService, "refresh").mockResolvedValue({
      access_token: "valid_jwt",
      token_type: "bearer",
      expires_in: 1800,
      user: userFixture("testuser"),
    });
    const logoutSpy = vi
      .spyOn(authService, "logout")
      .mockResolvedValue(undefined);

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
    });

    await userEvent.click(screen.getByTestId("logout-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
    expect(logoutSpy).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem("auth_token")).toBeNull();
  });
});
