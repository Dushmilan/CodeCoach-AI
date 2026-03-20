"use client";

import * as React from "react";

type Theme = "dark" | "light" | "system";

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
  attribute?: string;
  enableSystem?: boolean;
  disableTransitionOnChange?: boolean;
}

export function ThemeProvider({
  children,
  defaultTheme = "dark",
  storageKey = "ui-theme",
  attribute = "class",
  enableSystem = true,
  disableTransitionOnChange = false,
}: ThemeProviderProps) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    const storedTheme = localStorage.getItem(storageKey) as Theme | null;
    const initialTheme = storedTheme || defaultTheme;

    const root = document.documentElement;
    root.classList.remove("light", "dark");

    let actualTheme: string = initialTheme;
    if (initialTheme === "system" && enableSystem) {
      actualTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    root.classList.add(actualTheme);
  }, [defaultTheme, storageKey, enableSystem]);

  React.useEffect(() => {
    if (!mounted || defaultTheme !== "system" || !enableSystem) return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      const root = document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(mediaQuery.matches ? "dark" : "light");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mounted, defaultTheme, enableSystem]);

  React.useEffect(() => {
    if (disableTransitionOnChange && mounted) {
      const root = document.documentElement;
      root.style.setProperty("transition", "none");
      setTimeout(() => root.style.removeProperty("transition"), 0);
    }
  }, [disableTransitionOnChange, mounted]);

  return <>{children}</>;
}

export const useTheme = () => {
  const [theme, setThemeState] = React.useState<Theme>("dark");
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    const storedTheme = localStorage.getItem("ui-theme") as Theme | null;
    if (storedTheme) {
      setThemeState(storedTheme);
    }
  }, []);

  const setTheme = (newTheme: Theme) => {
    localStorage.setItem("ui-theme", newTheme);
    setThemeState(newTheme);

    const root = document.documentElement;
    root.classList.remove("light", "dark");

    let actualTheme: string = newTheme;
    if (newTheme === "system") {
      actualTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    root.classList.add(actualTheme);
  };

  if (!mounted) {
    return { theme: "dark", setTheme };
  }

  return { theme, setTheme };
};
