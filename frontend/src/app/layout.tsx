import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { ThemeProvider, AuthProvider, ToastProvider } from "@/providers";
import { UsageProvider } from "@/features/usage/usage.context";

export const metadata: Metadata = {
  title: "CodeCoach AI - Interview Practice Platform",
  description: "AI-powered coding interview practice with real-time coaching",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} font-sans`}
        suppressHydrationWarning
      >
        <ThemeProvider
          defaultTheme="dark"
          themes={["light", "dark"]}
          enableSystem={true}
          disableTransitionOnChange
          attribute="class"
        >
          <AuthProvider>
            <ToastProvider>
              <UsageProvider>{children}</UsageProvider>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
