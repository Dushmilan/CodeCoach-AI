'use client';

import { Header } from '@/components/header/Header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/providers/AuthProvider';
import { signInWithGoogle } from '@/features/auth/auth.service';
import { motion } from 'framer-motion';
import { Lock, LogIn, User } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError('');

      // Client-side validation
      if (username.length < 3) {
        setError('Username must be at least 3 characters');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }

      setIsLoading(true);
      try {
        await login(username, password);
        router.push('/');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Login failed');
      } finally {
        setIsLoading(false);
      }
    },
    [username, password, login, router],
  );

  const handleGoogle = useCallback(async () => {
    setError('');
    setIsGoogleLoading(true);
    try {
      await signInWithGoogle();
      // The browser is redirected to Supabase; no further action here.
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
      setIsGoogleLoading(false);
    }
  }, []);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex flex-col">
      <Header />

      <main className="flex-1 flex items-center justify-center px-4 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
          className="w-full max-w-sm"
        >
          <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
            <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-8">
              {/* Branding */}
              <div className="text-center mb-8">
                <div className="mb-4 flex justify-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
                    <LogIn className="h-6 w-6 text-primary/80" strokeWidth={1.5} />
                  </div>
                </div>
                <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">
                  Welcome back
                </h1>
                <p className="text-sm text-muted-foreground/60 mt-1.5">
                  Sign in to continue with CodeCoach AI
                </p>
              </div>

              <div className="space-y-4">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={handleGoogle}
                  disabled={isGoogleLoading}
                  aria-label="Continue with Google"
                >
                  {isGoogleLoading ? 'Redirecting...' : 'Continue with Google'}
                </Button>

                <div className="flex items-center gap-3 text-[11px] text-muted-foreground/40">
                  <span className="h-px flex-1 bg-white/[0.06]" />
                  or
                  <span className="h-px flex-1 bg-white/[0.06]" />
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <Input
                  id="username"
                  type="text"
                  label="Username"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  icon={User}
                  required
                  minLength={3}
                  maxLength={50}
                  autoComplete="username"
                />

                <Input
                  id="password"
                  type="password"
                  label="Password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  icon={Lock}
                  required
                  minLength={6}
                  autoComplete="current-password"
                />

                {error && (
                  <div className="text-xs text-red-400 bg-red-500/10 rounded-full px-4 py-2 text-center ring-1 ring-red-500/20">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full" disabled={isLoading} data-testid="login-submit">
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </Button>
              </form>

              <p className="text-center text-xs text-muted-foreground/60 mt-6">
                Don&apos;t have an account?{' '}
                <Link
                  href="/register"
                  className="text-primary/80 hover:text-primary transition-colors font-medium"
                >
                  Create one
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
