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
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            CodeCoach AI
          </Link>
          <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground">
            Sign in
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold">Create account</h1>
            <p className="text-sm text-muted-foreground mt-1">Start practicing with CodeCoach AI</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium mb-1">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                minLength={3}
                maxLength={50}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Choose a username"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="you@example.com"
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
                placeholder="At least 6 characters"
              />
            </div>

            {error && (
              <div className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
