'use client';

import { useState, useCallback } from 'react';

/**
 * Session-only settings.
 *
 * The NVIDIA API key is intentionally NOT persisted anywhere (no localStorage):
 * it is never sent to the backend — AI coaching uses the server-side
 * NVIDIA_API_KEY — so storing it would only widen the XSS blast radius.
 * The value lives for the current page session at most.
 */
export function useSettings() {
  const [apiKey, setApiKeyState] = useState<string>('');

  const setApiKey = useCallback((key: string) => {
    setApiKeyState(key);
  }, []);

  return { apiKey, setApiKey };
}
