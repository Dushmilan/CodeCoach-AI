import { describe, it, expect, vi, beforeEach } from "vitest";
import { AuthService } from "./auth.service";
import { HttpClient } from "@/lib/http-client";

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

describe("AuthService", () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: AuthService;

  beforeEach(() => {
    http = createMockHttp();
    service = new AuthService(http);
  });

  describe("login", () => {
    it("calls POST /api/auth/login with credentials", async () => {
      vi.mocked(http.post).mockResolvedValue({
        access_token: "jwt",
        token_type: "bearer",
        expires_in: 86400,
        user: {
          id: "1",
          username: "u",
          email: "u@t.com",
          created_at: "2024-01-01",
          is_active: true,
        },
      });

      await service.login({ username: "u", password: "p" });

      expect(http.post).toHaveBeenCalledWith("/api/auth/login", {
        username: "u",
        password: "p",
      });
    });

    it("returns token response on success", async () => {
      const mockResponse = {
        access_token: "jwt_token",
        token_type: "bearer",
        expires_in: 86400,
        user: {
          id: "1",
          username: "u",
          email: "u@t.com",
          created_at: "2024-01-01",
          is_active: true,
        },
      };
      vi.mocked(http.post).mockResolvedValue(mockResponse);

      const result = await service.login({ username: "u", password: "p" });

      expect(result.access_token).toBe("jwt_token");
      expect(result.user.username).toBe("u");
    });

    it("throws on invalid credentials", async () => {
      vi.mocked(http.post).mockRejectedValue(
        new Error("Invalid username or password"),
      );

      await expect(
        service.login({ username: "u", password: "wrong" }),
      ).rejects.toThrow("Invalid username or password");
    });
  });

  describe("register", () => {
    it("calls POST /api/auth/register with user data", async () => {
      vi.mocked(http.post).mockResolvedValue({
        access_token: "jwt",
        token_type: "bearer",
        expires_in: 86400,
        user: {
          id: "1",
          username: "new",
          email: "n@t.com",
          created_at: "2024-01-01",
          is_active: true,
        },
      });

      await service.register({
        username: "new",
        email: "n@t.com",
        password: "pass",
      });

      expect(http.post).toHaveBeenCalledWith("/api/auth/register", {
        username: "new",
        email: "n@t.com",
        password: "pass",
      });
    });
  });

  describe("loginWithSupabase", () => {
    it("calls POST /api/auth/supabase with access token", async () => {
      vi.mocked(http.post).mockResolvedValue({
        access_token: "jwt",
        token_type: "bearer",
        expires_in: 86400,
        user: {
          id: "1",
          username: "u",
          email: "u@t.com",
          created_at: "2024-01-01",
          is_active: true,
        },
      });

      await service.loginWithSupabase({ access_token: "supabase_token" });

      expect(http.post).toHaveBeenCalledWith("/api/auth/supabase", {
        access_token: "supabase_token",
      });
    });
  });

  describe("refresh", () => {
    it("calls POST /api/auth/refresh with refresh token", async () => {
      vi.mocked(http.post).mockResolvedValue({
        access_token: "new_jwt",
        refresh_token: "rotated_refresh",
        token_type: "bearer",
        expires_in: 1800,
        user: {
          id: "1",
          username: "u",
          email: "u@t.com",
          created_at: "2024-01-01",
          is_active: true,
        },
      });

      const result = await service.refresh();

      expect(http.post).toHaveBeenCalledWith("/api/auth/refresh", {});
      expect(result.access_token).toBe("new_jwt");
      expect(result.refresh_token).toBe("rotated_refresh");
    });
  });

  describe("getMe", () => {
    it("calls GET /api/auth/me with Authorization header", async () => {
      vi.mocked(http.get).mockResolvedValue({
        id: "1",
        username: "u",
        email: "u@t.com",
        created_at: "2024-01-01",
        is_active: true,
      });

      await service.getMe("my_token");

      expect(http.get).toHaveBeenCalledWith("/api/auth/me", {
        headers: { Authorization: "Bearer my_token" },
      });
    });
  });
});
