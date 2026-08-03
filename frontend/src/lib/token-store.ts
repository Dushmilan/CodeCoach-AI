/**
 * Single source of truth for auth token storage.
 *
 * Security model:
 *  - The refresh token lives ONLY in an HttpOnly cookie set by the backend
 *    (never in localStorage, so XSS cannot read it).
 *  - The short-lived access token is held in memory. On page load the app
 *    exchanges the refresh cookie for a fresh access token via /api/auth/refresh.
 *
 * This module replaces the duplicated getAuthToken/setAuthTokens helpers in
 * fetch-client.ts and getStoredToken/setStoredTokens in AuthProvider.tsx.
 */

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearTokens(): void {
  accessToken = null;
}
