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

  async loginWithSupabase(data: SupabaseAuthRequest): Promise<TokenResponse> {
    return this.http.post<TokenResponse>("/api/auth/supabase", data);
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

/**
 * Start the Supabase Google OAuth flow (authorization-code + PKCE).
 *
 * Redirects the browser to the Supabase authorization endpoint; on success
 * Supabase redirects back to `<origin>/auth/callback` with a `code`, which
 * the callback page exchanges and hands to the backend for verification.
 */
export async function signInWithGoogle(): Promise<void> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  }

  const { createBrowserClient } = await import("@supabase/ssr");
  const supabase = createBrowserClient(supabaseUrl, supabaseKey);
  const redirectTo = `${window.location.origin}/auth/callback`;

  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo },
  });
  if (error) throw error;
}
