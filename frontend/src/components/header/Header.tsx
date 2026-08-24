'use client';

import { SettingsModal } from '@/components/settings/SettingsModal';
import { cn } from '@/lib/utils';
import { useAuth } from '@/providers';
import { Code, GraduationCap, Moon, Settings, Sun, User, X } from 'lucide-react';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import * as React from 'react';
import { useEffect, useState } from 'react';

export function Header() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { user, isAuthenticated, logout, isHydrated } = useAuth();
  const [showSettings, setShowSettings] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // ... (lines 33-40)

  return (
    <>
      {/* Fluid Island Nav */}
      <header
        className={cn(
          'relative z-30 mx-auto mt-4 w-max rounded-full bg-card/70 backdrop-blur-2xl ring-1 ring-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]',
          menuOpen && 'scale-95 opacity-0 pointer-events-none',
        )}
      >
        <div className="flex items-center gap-1 px-2 py-1.5">
          <Link
            href="/"
            className="px-4 py-2 text-sm font-semibold tracking-tight text-foreground/90 hover:text-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
          >
            CodeCoach AI
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-0.5 ml-2">
            <Link
              href="/problems"
              className="px-3 py-1.5 text-xs text-muted-foreground/70 hover:text-foreground hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] flex items-center gap-1.5"
            >
              <Code className="h-3 w-3" />
              Problems
            </Link>
            <Link
              href="/learn"
              className="px-3 py-1.5 text-xs text-muted-foreground/70 hover:text-foreground hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] flex items-center gap-1.5"
            >
              <GraduationCap className="h-3 w-3" />
              Learn
            </Link>
          </nav>

          <div className="flex items-center gap-0.5 ml-2">
            {isHydrated ? (
              isAuthenticated ? (
                <span className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground">
                  <User className="h-3 w-3" />
                  {user?.username}
                </span>
              ) : (
                <Link href="/login" data-testid="header-signin-link">
                  <button data-testid="header-signin" className="px-3 py-1.5 text-xs text-muted-foreground/70 hover:text-foreground hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]">
                    Sign in
                  </button>
                </Link>
              )
            ) : (
              <div className="w-16 h-6 rounded-full bg-white/5 animate-pulse" />
            )}

            <button
              onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
              className="p-2 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              aria-label="Toggle theme"
            >
              {mounted ? (
                resolvedTheme === 'dark' ? (
                  <Sun className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <Moon className="h-3.5 w-3.5 text-muted-foreground" />
                )
              ) : (
                <div className="h-3.5 w-3.5" />
              )}
            </button>

            <button
              onClick={() => setShowSettings(true)}
              className="p-2 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              title="Settings"
            >
              <Settings className="h-3.5 w-3.5 text-muted-foreground" />
            </button>

            {/* Hamburger */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden relative w-9 h-9 flex items-center justify-center hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              aria-label="Toggle menu"
            >
              <div className="relative w-4 h-3.5">
                <span
                  className={cn(
                    'absolute left-0 top-0 block h-[1.5px] w-full bg-foreground/60 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
                    menuOpen && 'top-1/2 -translate-y-1/2 rotate-45',
                  )}
                />
                <span
                  className={cn(
                    'absolute left-0 top-1/2 -translate-y-1/2 block h-[1.5px] w-full bg-foreground/60 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
                    menuOpen && 'opacity-0 scale-x-0',
                  )}
                />
                <span
                  className={cn(
                    'absolute left-0 bottom-0 block h-[1.5px] w-full bg-foreground/60 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
                    menuOpen && 'bottom-1/2 translate-y-1/2 -rotate-45',
                  )}
                />
              </div>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <div
        className={cn(
          'fixed inset-0 z-50 flex flex-col items-center justify-center backdrop-blur-3xl bg-black/90 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]',
          menuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        )}
      >
        <button
          onClick={() => setMenuOpen(false)}
          className="absolute top-6 right-6 p-3 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
          aria-label="Close menu"
        >
          <X className="h-5 w-5 text-white/70" />
        </button>

        <nav className="flex flex-col items-center gap-6">
          {[
            { href: '/', label: 'Home', delay: 'delay-100' },
            { href: '/problems', label: 'Problems', delay: 'delay-115' },
            { href: '/learn', label: 'Learn', delay: 'delay-125' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={cn(
                'text-4xl font-light tracking-tight text-white/80 hover:text-white transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]',
                menuOpen ? `translate-y-0 opacity-100 ${link.delay}` : 'translate-y-12 opacity-0',
              )}
              style={{
                transitionProperty: 'transform, opacity',
              }}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div
          className={cn(
            'absolute bottom-12 flex items-center gap-4 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] delay-300',
            menuOpen ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0',
          )}
        >
          {isHydrated && isAuthenticated && (
            <span className="text-sm text-white/40 flex items-center gap-2">
              <User className="h-3.5 w-3.5" />
              {user?.username}
            </span>
          )}
          <button
            onClick={() => {
              setShowSettings(true);
              setMenuOpen(false);
            }}
            className="px-5 py-2 text-sm text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
          >
            Settings
          </button>
          <button
            onClick={() => {
              setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
              setMenuOpen(false);
            }}
            className="px-5 py-2 text-sm text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
          >
            {mounted ? (resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode') : 'Theme'}
          </button>
        </div>
      </div>

      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        isAuthenticated={isHydrated && isAuthenticated}
        onLogout={logout}
        plan={user?.plan}
      />
    </>
  );
}
