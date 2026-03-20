"use client";

import * as React from "react";

type Theme = "dark" | "light" | "system";

export function useTheme() {
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
    return { theme: "dark" as Theme, setTheme };
  }

  return { theme, setTheme };
}
