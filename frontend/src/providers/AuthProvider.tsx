'use client';

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { User, AuthState } from '@/types';
import { authService } from '@/features/auth/auth.service';
import { showToast } from '@/components/ui/Toast';
import { getAccessToken, setAccessToken, clearTokens } from '@/lib/token-store';

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
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

  const setAuth = useCallback(
    (user: User | null, token: string | null, _refreshToken?: string | null) => {
      setState({
        user,
        token,
        isLoading: false,
        isAuthenticated: !!user && !!token,
        isHydrated: true,
      });
      setAccessToken(token);
    },
    [],
  );

  useEffect(() => {
    const storedToken = getAccessToken();
    if (!storedToken) {
      // No in-memory token. Try to exchange the HttpOnly refresh cookie for a
      // fresh access token (silent re-authentication on page load).
      authService
        .refresh()
        .then((tokens) => {
          setAccessToken(tokens.access_token);
          return authService.getMe(tokens.access_token);
        })
        .then((user) => {
          const token = getAccessToken();
          setState({
            user,
            token,
            isLoading: false,
            isAuthenticated: true,
            isHydrated: true,
          });
        })
        .catch(() => {
          clearTokens();
          setState({
            user: null,
            token: null,
            isLoading: false,
            isAuthenticated: false,
            isHydrated: true,
          });
        });
      return;
    }

    authService
      .getMe(storedToken)
      .then((user) => {
        setState({
          user,
          token: storedToken,
          isLoading: false,
          isAuthenticated: true,
          isHydrated: true,
        });
      })
      .catch(() => {
        clearTokens();
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
      setAuth(response.user, response.access_token, response.refresh_token ?? null);
      showToast('Signed in successfully', 'success');
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
      setAuth(response.user, response.access_token, response.refresh_token ?? null);
      showToast('Account created successfully', 'success');
    },
    [setAuth],
  );

  const loginWithSupabase = useCallback(
    async (accessToken: string) => {
      const response = await authService.loginWithSupabase({
        access_token: accessToken,
      });
      setAuth(response.user, response.access_token, response.refresh_token ?? null);
    },
    [setAuth],
  );

  const logout = useCallback(() => {
    clearTokens();
    setAuth(null, null, null);
    authService.logout().catch(() => {});
    showToast('Signed out', 'info');
  }, [setAuth]);

  return (
    <AuthContext.Provider value={{ ...state, login, register, loginWithSupabase, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
