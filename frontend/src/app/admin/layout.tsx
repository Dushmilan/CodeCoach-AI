'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MenuIcon, XIcon, SunIcon, MoonIcon, SettingsIcon } from '@/components/ui/icons';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { useAuth } from '@/providers';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { useSettings } from '@/hooks/use-settings';

import AdminSidebar from '@/components/admin/AdminSidebar';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === '/admin/login';
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { apiKey, setApiKey } = useSettings();
  const { user, isAuthenticated, logout, isHydrated } = useAuth();
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isLoginPage && (!isAuthenticated || !['admin', 'super_admin'].includes(user?.role ?? ''))) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-muted-foreground">You need admin privileges to access this area.</p>
        </div>
      </div>
    );
  }

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background relative">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setShowMobileMenu(!showMobileMenu)}
        className="md:hidden fixed top-4 right-4 z-50 p-3 rounded-lg bg-card border border-border shadow-lg"
        aria-label="Toggle mobile admin menu"
      >
        {showMobileMenu ? <XIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
      </button>

      {/* Mobile Overlay */}
      {showMobileMenu && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={() => setShowMobileMenu(false)}
        />
      )}

      {/* Sidebar */}
      <AdminSidebar open={showMobileMenu} onClose={() => setShowMobileMenu(false)} />

      {/* Main Content */}
      <div className="md:ml-64 min-h-screen">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur sticky top-0 z-30">
          <div className="flex items-center justify-between h-full px-6">
            <div className="flex items-center gap-4">
              <Link href="/admin" className="font-bold text-xl">
                CodeCoach <span className="text-primary">AI</span> Admin
              </Link>
            </div>

            <div className="flex items-center gap-2">
              {/* User Info */}
              <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/50">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {user?.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{user?.username}</span>
                  <span className="text-xs text-muted-foreground">{user?.role}</span>
                </div>
              </div>

              {/* Settings */}
              <button
                onClick={() => setSettingsOpen(true)}
                className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                aria-label="Open settings"
              >
                <SettingsIcon className="h-4 w-4" />
              </button>

              {/* Theme Toggle */}
              <button
                onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                aria-label="Toggle theme"
              >
                {mounted ? (
                  resolvedTheme === 'dark' ? (
                    <SunIcon className="h-4 w-4" />
                  ) : (
                    <MoonIcon className="h-4 w-4" />
                  )
                ) : (
                  <div className="h-4 w-4" />
                )}
              </button>

              {/* Settings Modal */}
              <SettingsModal
                open={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                apiKey={apiKey}
                onSave={setApiKey}
                isAuthenticated={isAuthenticated}
                onLogout={logout}
              />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
