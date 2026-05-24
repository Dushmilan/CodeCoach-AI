import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider, AuthProvider, ToastProvider } from "@/providers";

const inter = Inter({ subsets: ["latin"] });

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
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <AuthProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}