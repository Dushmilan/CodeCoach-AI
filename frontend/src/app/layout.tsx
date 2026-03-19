import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { ThemeProvider } from 'next-themes';
import Script from 'next/script';
import './globals.css';
import '@/styles/themes.css';
import { CodeCoachProvider } from '@/contexts/CodeCoachContext';
import { Header } from '@/components/Header';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetBrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains-mono' });

export const metadata: Metadata = {
  title: 'CodeCoach AI - Learn to Code with AI',
  description: 'Master coding with AI-powered guidance and interactive problem solving',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Script id="theme-script" strategy="beforeInteractive">
          {`
            (function() {
              function setThemeColor() {
                const theme = localStorage.getItem('theme') || 'system';
                const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                const currentTheme = theme === 'system' ? systemTheme : theme;
                
                const meta = document.querySelector('meta[name="theme-color"]');
                if (meta) {
                  meta.setAttribute('content', currentTheme === 'dark' ? '#0a0a0a' : '#ffffff');
                }
              }
              
              setThemeColor();
              
              const observer = new MutationObserver(() => {
                setThemeColor();
              });
              
              observer.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['class']
              });
            })();
          `}
        </Script>
      </head>
      <body className={`${inter.variable} ${jetBrainsMono.variable} font-sans`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <CodeCoachProvider>
            <div className="flex flex-col h-screen bg-background text-foreground">
              <Header />
              <main className="flex-1 overflow-hidden">
                {children}
              </main>
            </div>
          </CodeCoachProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}