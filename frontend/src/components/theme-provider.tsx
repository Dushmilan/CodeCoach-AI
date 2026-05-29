"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

// We can just use the type from the library or let it be inferred if necessary.
// Or define it locally if importing from dist/types is failing.
// The error TS2307 suggests it can't find types, so let's use a simpler import.
type ThemeProviderProps = React.ComponentProps<typeof NextThemesProvider>;

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
