'use client';

import { ThemeProvider as CustomThemeProvider, useTheme } from '@/components/theme-provider';

export function ClientThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <CustomThemeProvider
      defaultTheme="dark"
      enableSystem={false}
      disableTransitionOnChange
    >
      {children}
    </CustomThemeProvider>
  );
}

export { useTheme };
