import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthProvider";
import { authService } from "@/features/auth/auth.service";

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

const storage = new Map<string, string>();

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>,
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, value),
      removeItem: (key: string) => storage.delete(key),
      clear: () => storage.clear(),
    });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows loading state while restoring token", () => {
    storage.set("auth_token", JSON.stringify("stored_jwt"));
    vi.spyOn(authService, "getMe").mockImplementation(
      () => new Promise(() => {}),
    );
    renderWithProvider();
    expect(screen.getByText("Loading...")).toBeDefined();
  });

  it("shows logged out when no token in storage", async () => {
    vi.spyOn(authService, "getMe").mockRejectedValue(new Error("No token"));
    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
  });

  it("restores session when valid token in storage", async () => {
    localStorage.setItem("auth_token", JSON.stringify("valid_jwt"));
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
    localStorage.setItem("auth_token", JSON.stringify("expired_jwt"));
    vi.spyOn(authService, "getMe").mockRejectedValue(
      new Error("Token expired"),
    );

    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId("auth-status").textContent).toBe("Logged out");
    });
    expect(localStorage.getItem("auth_token")).toBeNull();
  });

  it("login sets user and token", async () => {
    vi.spyOn(authService, "getMe").mockRejectedValue(new Error("No token"));
    vi.spyOn(authService, "login").mockResolvedValue({
      access_token: "new_jwt",
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
    expect(localStorage.getItem("auth_token")).toBe(JSON.stringify("new_jwt"));
  });

  it("logout clears user and token", async () => {
    localStorage.setItem("auth_token", JSON.stringify("valid_jwt"));
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
    expect(localStorage.getItem("auth_token")).toBeNull();
  });
});
