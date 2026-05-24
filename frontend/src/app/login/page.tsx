'use client';

import { useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/button';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginWithSupabase } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const redirectTo = searchParams.get('redirect') || '/';
  const actionHint = searchParams.get('action');
  const actionLabel = actionHint ? { run: 'run code', submit: 'submit code', coach: 'use the AI Coach' }[actionHint] : null;

  const supabaseUrl = typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_SUPABASE_URL : undefined;
  const hasSupabase = !!(supabaseUrl && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(username, password);
      router.push(redirectTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  }, [username, password, login, router, redirectTo]);

  const handleGoogleLogin = useCallback(async () => {
    if (!hasSupabase) return;
    setError('');
    try {
      const { createBrowserClient } = await import('@supabase/ssr');
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      );
      const { error: authError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: `${window.location.origin}/auth/callback` },
      });
      if (authError) setError(authError.message);
    } catch {
      setError('Failed to initiate Google sign in');
    }
  }, [hasSupabase]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            CodeCoach AI
          </Link>
          <Link href="/register" className="text-sm text-muted-foreground hover:text-foreground">
            Create account
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold">Sign in</h1>
            <p className="text-sm text-muted-foreground mt-1">
              {actionLabel ? `Sign in to ${actionLabel}` : 'Welcome back to CodeCoach AI'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium mb-1">Username or email</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="username@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full"
            onClick={handleGoogleLogin}
            disabled={!hasSupabase}
            title={!hasSupabase ? 'Set SUPABASE_URL and SUPABASE_ANON_KEY to enable' : undefined}
          >
            {hasSupabase ? 'Sign in with Google' : 'Google sign in (configure Supabase)'}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-primary hover:underline">
              Register
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
