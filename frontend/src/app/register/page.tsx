'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/providers/AuthProvider';
import { Button } from '@/components/ui/button';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await register(username, email, password);
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  }, [username, email, password, register, router]);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex flex-col">
      {/* Fluid Island Nav */}
      <div className="flex items-center justify-center pt-6">
        <div className="inline-flex items-center gap-4 px-5 py-2 rounded-full bg-card/70 backdrop-blur-2xl ring-1 ring-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]">
          <Link href="/" className="text-sm font-semibold tracking-tight text-foreground/90">
            CodeCoach AI
          </Link>
          <Link href="/login" className="text-xs text-muted-foreground/70 hover:text-foreground hover:bg-white/5 px-3 py-1 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]">
            Sign in
          </Link>
        </div>
      </div>

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-8">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">Create account</h1>
              <p className="text-sm text-muted-foreground/60 mt-1.5">Start practicing with CodeCoach AI</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">Username</label>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    minLength={3}
                    maxLength={50}
                    className="w-full px-3 py-2 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 rounded-[calc(1rem-0.125rem)] focus:outline-none"
                    placeholder="Choose a username"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">Email</label>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 rounded-[calc(1rem-0.125rem)] focus:outline-none"
                    placeholder="you@example.com"
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
                    placeholder="At least 6 characters"
                  />
                </div>
              </div>

              {error && (
                <div className="text-xs text-red-400 bg-red-500/10 rounded-full px-4 py-2 text-center">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Creating account...' : 'Create account'}
              </Button>
            </form>

            <p className="text-center text-xs text-muted-foreground/60 mt-6">
              Already have an account?{' '}
              <Link href="/login" className="text-primary/80 hover:text-primary transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
