'use client';

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { User, AuthState } from '@/types';
import { authService } from '@/features/auth/auth.service';
import { showToast } from '@/components/ui/Toast';

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  loginWithSupabase: (accessToken: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem('auth_token');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function setStoredToken(token: string | null) {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem('auth_token', JSON.stringify(token));
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const setAuth = useCallback((user: User | null, token: string | null) => {
    setState({
      user,
      token,
      isLoading: false,
      isAuthenticated: !!user && !!token,
    });
    setStoredToken(token);
  }, []);

  useEffect(() => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      setState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    authService.getMe(storedToken)
      .then(user => {
        setState({
          user,
          token: storedToken,
          isLoading: false,
          isAuthenticated: true,
        });
      })
      .catch(() => {
        setStoredToken(null);
        setState({
          user: null,
          token: null,
          isLoading: false,
          isAuthenticated: false,
        });
      });
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await authService.login({ username, password });
    setAuth(response.user, response.access_token);
    showToast('Signed in successfully', 'success');
  }, [setAuth]);

  const register = useCallback(async (username: string, email: string, password: string) => {
    const response = await authService.register({ username, email, password });
    setAuth(response.user, response.access_token);
    showToast('Account created successfully', 'success');
  }, [setAuth]);

  const loginWithSupabase = useCallback(async (accessToken: string) => {
    const response = await authService.loginWithSupabase({ access_token: accessToken });
    setAuth(response.user, response.access_token);
  }, [setAuth]);

  const logout = useCallback(() => {
    setAuth(null, null);
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
