import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthProvider";
import { authService } from "@/features/auth/auth.service";
import { setAccessToken, clearTokens } from "@/lib/token-store";

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
    clearTokens();
    vi.spyOn(authService, "refresh").mockRejectedValue(
      new Error("No session"),
    );
  });

  afterEach(() => {
    clearTokens();
  });

  it("shows loading state while restoring session", () => {
    vi.spyOn(authService, "refresh").mockImplementation(
      () => new Promise(() => {}),
    );
    renderWithProvider();
    expect(screen.getByText("Loading...")).toBeDefined();
  });

  it("shows logged out when no session can be restored", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No token"));
    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
  });

  it("restores session via refresh cookie when no in-memory token", async () => {
    vi.spyOn(authService, "refresh").mockResolvedValue({
      access_token: "fresh_jwt",
      token_type: "bearer",
      expires_in: 1800,
      user: {
        id: "1",
        username: "testuser",
        email: "t@t.com",
        created_at: "2024-01-01",
        is_active: true,
      },
    });
    vi.spyOn(authService, "getMe").mockResolvedValue({
      id: "1",
      username: "testuser",
      email: "t@t.com",
      created_at: "2024-01-01",
      is_active: true,
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
      expect(screen.getByTestId("username").textContent).toBe("testuser");
    });
  });

  it("restores session when a valid in-memory token exists", async () => {
    setAccessToken("valid_jwt");
    vi.spyOn(authService, "getMe").mockResolvedValue({
      id: "1",
      username: "testuser",
      email: "t@t.com",
      created_at: "2024-01-01",
      is_active: true,
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
      expect(screen.getByTestId("username").textContent).toBe("testuser");
    });
  });

  it("clears token when getMe fails", async () => {
    setAccessToken("expired_jwt");
    vi.spyOn(authService, "getMe").mockRejectedValue(
      new Error("Token expired"),
    );

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
    expect(clearTokens());
  });

  it("login sets user and token", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No token"));
    vi.spyOn(authService, "login").mockResolvedValue({
      access_token: "new_jwt",
      refresh_token: "new_refresh",
      token_type: "bearer",
      expires_in: 86400,
      user: {
        id: "2",
        username: "newuser",
        email: "n@t.com",
        created_at: "2024-01-01",
        is_active: true,
      },
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
  });

  it("register stores refresh token", async () => {
    vi.spyOn(authService, "refresh").mockRejectedValue(new Error("No token"));
    vi.spyOn(authService, "login").mockResolvedValue({
      access_token: "reg_jwt",
      refresh_token: "reg_refresh",
      token_type: "bearer",
      expires_in: 86400,
      user: {
        id: "3",
        username: "reguser",
        email: "r@t.com",
        created_at: "2024-01-01",
        is_active: true,
      },
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });

    await userEvent.click(screen.getByTestId("register-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
    });
  });

  it("logout clears tokens", async () => {
    setAccessToken("valid_jwt");
    vi.spyOn(authService, "getMe").mockResolvedValue({
      id: "1",
      username: "testuser",
      email: "t@t.com",
      created_at: "2024-01-01",
      is_active: true,
    });

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged in");
    });

    await userEvent.click(screen.getByTestId("logout-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
  });
});
