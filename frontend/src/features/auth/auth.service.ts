import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { User } from "@/types";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  refresh_token?: string | null;
  csrf_token?: string | null;
}

export class AuthService {
  constructor(private http: HttpClient) {}

  async login(data: LoginRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/login", data);
  }

  async register(data: RegisterRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/register", data);
  }

  async refresh(): Promise<TokenResponse> {
    // SEC-2: the refresh token lives in an httpOnly cookie owned by the
    // backend; the browser attaches it automatically. No body needed.
    return this.http.post<TokenResponse>("/api/auth/refresh", undefined, {
      skipAuthRefresh: true,
    });
  }

  async logout(): Promise<void> {
    // POST (mutating) -> fetch-client attaches the X-CSRF-Token header from
    // the csrf_token cookie when a session cookie is present.
    await this.http.post<Record<string, unknown>>("/api/auth/logout");
  }

  async getMe(token: string): Promise<User> {
    return this.http.get<User>("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}

export const authService = new AuthService(new FetchClient());
