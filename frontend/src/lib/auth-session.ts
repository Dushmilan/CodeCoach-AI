/**
 * In-memory auth session store.
 *
 * SEC-2: access tokens live ONLY in memory (never localStorage) so a single
 * XSS can't exfiltrate a persistent credential. The refresh token lives in an
 * httpOnly cookie owned by the backend and is never visible to JS.
 */

let accessToken: string | null = null;
let csrfToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * CSRF token for the double-submit pattern.
 *
 * The backend sets a JS-readable `csrf_token` cookie on its OWN origin; the
 * frontend is cross-origin so `document.cookie` can't see it. The backend also
 * returns the token in login/refresh response bodies — that value is stored
 * here in memory and echoed as the X-CSRF-Token header.
 */
export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}
