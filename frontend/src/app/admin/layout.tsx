'use client';

import { SettingsModal } from '@/components/settings/SettingsModal';
import { useAuth } from '@/providers';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Menu, Moon, Settings, Sun, X } from 'lucide-react';
import { MotionConfig } from 'framer-motion';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useEffect, useState } from 'react';

import AdminSidebar from '@/components/admin/AdminSidebar';
import { RoleGuard } from '@/components/auth/RoleGuard';

function AdminContent({ children }: { children: React.ReactNode }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen bg-background relative">
        {/* Mobile Menu Button */}
        <button
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          className="md:hidden fixed top-4 right-4 z-50 p-3 rounded-full bg-card border border-border shadow-lg"
          aria-label="Toggle mobile admin menu"
        >
          {showMobileMenu ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
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
            <div className="flex items-center justify-between h-full px-4 md:px-6">
              <div className="flex items-center gap-4">
                <Link href="/admin" className="font-bold text-xl">
                  CodeCoach <span className="text-brand">AI</span> Admin
                </Link>
              </div>

              <div className="flex items-center gap-2">
                {/* User Info */}
                <div className="hidden md:flex items-center gap-2 rounded-full bg-muted/50 py-1 pl-1 pr-4">
                  <Avatar data-testid="admin-header-avatar" className="h-8 w-8">
                    <AvatarFallback>
                      {user?.username.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{user?.username}</span>
                    <span className="text-xs text-muted-foreground">{user?.role}</span>
                  </div>
                </div>

                {/* Settings */}
                <button
                  onClick={() => setSettingsOpen(true)}
                  className="p-2.5 rounded-full bg-muted/50 hover:bg-muted transition-colors"
                  aria-label="Open settings"
                >
                  <Settings className="h-4 w-4" />
                </button>

                {/* Theme Toggle */}
                <button
                  onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                  className="p-2.5 rounded-full bg-muted/50 hover:bg-muted transition-colors"
                  aria-label="Toggle theme"
                >
                  {mounted ? (
                    resolvedTheme === 'dark' ? (
                      <Sun className="h-4 w-4" />
                    ) : (
                      <Moon className="h-4 w-4" />
                    )
                  ) : (
                    <div className="h-4 w-4" />
                  )}
                </button>

                {/* Settings Modal */}
                <SettingsModal
                  open={settingsOpen}
                  onClose={() => setSettingsOpen(false)}
                  isAuthenticated={isAuthenticated}
                  onLogout={logout}
                />
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="p-4 md:p-8">{children}</main>
        </div>
      </div>
    </MotionConfig>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === '/admin/login';

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <RoleGuard
      allowedRoles={['professor', 'admin', 'super_admin']}
      loginHref="/admin/login"
      deniedMessage="You need admin privileges to access this area."
    >
      <AdminContent>{children}</AdminContent>
    </RoleGuard>
  );
}
