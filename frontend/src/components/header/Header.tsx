'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Moon, Sun, Settings, LogOut, User } from 'lucide-react';
import { useTheme } from '@/hooks';
import { useAuth } from '@/providers';
import { Button } from '@/components/ui/button';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { useSettings } from '@/hooks/use-settings';

export function Header() {
  const { theme, setTheme } = useTheme();
  const { apiKey, setApiKey } = useSettings();
  const { user, isAuthenticated, logout } = useAuth();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-4">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            CodeCoach AI
          </Link>
          <nav className="hidden sm:flex items-center space-x-1 ml-6">
            <Link
              href="/privacy"
              className="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-md hover:bg-secondary transition-colors"
            >
              Privacy
            </Link>
            <Link
              href="/educators"
              className="text-sm text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-md hover:bg-secondary transition-colors"
            >
              For Educators
            </Link>
          </nav>
        </div>

        <div className="flex items-center space-x-2">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground hidden sm:inline-flex items-center gap-1">
                <User className="h-3.5 w-3.5" />
                {user?.username}
              </span>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="hover:bg-secondary"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Link href="/login">
              <Button variant="ghost" size="sm" className="hover:bg-secondary">
                Sign in
              </Button>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowSettings(true)}
            className="hover:bg-secondary"
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="hover:bg-secondary"
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      <SettingsModal
        open={showSettings}
        onClose={() => setShowSettings(false)}
        apiKey={apiKey}
        onSave={setApiKey}
      />
    </header>
  );
}
