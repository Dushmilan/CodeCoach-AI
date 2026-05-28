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
    <div className="min-h-[100dvh] bg-background text-foreground flex flex-col">


      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-8">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">Sign in</h1>
              <p className="text-sm text-muted-foreground/60 mt-1.5">
                {actionLabel ? `Sign in to ${actionLabel}` : 'Welcome back to CodeCoach AI'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">Username or email</label>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 rounded-[calc(1rem-0.125rem)] focus:outline-none"
                    placeholder="username@example.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">Password</label>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={6}
                    className="w-full px-3 py-2 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 rounded-[calc(1rem-0.125rem)] focus:outline-none"
                    placeholder="Enter your password"
                  />
                </div>
              </div>

              {error && (
                <div className="text-xs text-red-400 bg-red-500/10 rounded-full px-4 py-2 text-center">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-white/5" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-wide">
                <span className="bg-card px-3 text-muted-foreground/40">Or continue with</span>
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

            <p className="text-center text-xs text-muted-foreground/60 mt-6">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-primary/80 hover:text-primary transition-colors">
                Register
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
