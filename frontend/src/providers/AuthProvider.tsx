"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { User, AuthState } from "@/types";
import { authService } from "@/features/auth/auth.service";
import { setAccessToken, setCsrfToken } from "@/lib/auth-session";
import { showToast } from "@/components/ui/Toast";

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
  ) => Promise<void>;
  loginWithSupabase: (accessToken: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
    isHydrated: false,
  });

  const setAuth = useCallback((user: User | null, token: string | null) => {
    setAccessToken(token);
    setState({
      user,
      token,
      isLoading: false,
      isAuthenticated: !!user && !!token,
      isHydrated: true,
    });
  }, []);

  useEffect(() => {
    // SEC-2: no tokens in localStorage. The refresh token is an httpOnly
    // cookie; exchanging it for a fresh access token restores the session.
    authService
      .refresh()
      .then((response) => {
        setAccessToken(response.access_token);
        setCsrfToken(response.csrf_token ?? null);
        setState({
          user: response.user,
          token: response.access_token,
          isLoading: false,
          isAuthenticated: true,
          isHydrated: true,
        });
      })
      .catch(() => {
        setAccessToken(null);
        setCsrfToken(null);
        setState({
          user: null,
          token: null,
          isLoading: false,
          isAuthenticated: false,
          isHydrated: true,
        });
      });
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const response = await authService.login({ username, password });
      setCsrfToken(response.csrf_token ?? null);
      setAuth(response.user, response.access_token);
      showToast("Signed in successfully", "success");
    },
    [setAuth],
  );

  const register = useCallback(
    async (username: string, email: string, password: string) => {
      const response = await authService.register({
        username,
        email,
        password,
      });
      setCsrfToken(response.csrf_token ?? null);
      setAuth(response.user, response.access_token);
      showToast("Account created successfully", "success");
    },
    [setAuth],
  );

  const loginWithSupabase = useCallback(
    async (accessToken: string) => {
      const response = await authService.loginWithSupabase({
        access_token: accessToken,
      });
      setCsrfToken(response.csrf_token ?? null);
      setAuth(response.user, response.access_token);
    },
    [setAuth],
  );

  const logout = useCallback(() => {
    // Best-effort: clear the httpOnly refresh cookie server-side first.
    authService
      .logout()
      .catch(() => {
        // Even if the network call fails, local state must clear.
      })
      .finally(() => {
        setCsrfToken(null);
        setAuth(null, null);
        showToast("Signed out", "info");
      });
  }, [setAuth]);

  return (
    <AuthContext.Provider
      value={{ ...state, login, register, loginWithSupabase, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
