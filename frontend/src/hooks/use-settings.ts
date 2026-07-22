"use client";

import { useState, useCallback, useEffect } from "react";

const API_KEY_KEY = "nvidia_api_key";

export function useSettings() {
  const [apiKey, setApiKeyState] = useState<string>("");

  useEffect(() => {
    setApiKeyState(localStorage.getItem(API_KEY_KEY) || "");
  }, []);

  const setApiKey = useCallback((key: string) => {
    setApiKeyState(key);
    if (key) {
      localStorage.setItem(API_KEY_KEY, key);
    } else {
      localStorage.removeItem(API_KEY_KEY);
    }
  }, []);

  return { apiKey, setApiKey };
}
