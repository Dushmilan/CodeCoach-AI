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

export interface SupabaseAuthRequest {
  access_token: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  refresh_token?: string | null;
}

export class AuthService {
  constructor(private http: HttpClient) {}

  async login(data: LoginRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/login", data);
  }

  async register(data: RegisterRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/register", data);
  }

  async loginWithSupabase(data: SupabaseAuthRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/supabase", data);
  }

  async refresh(refreshToken: string): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/refresh", {
      refresh_token: refreshToken,
    });
  }

  async getMe(token: string): Promise<User> {
    return this.http.get<User>("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}

export const authService = new AuthService(new FetchClient());
