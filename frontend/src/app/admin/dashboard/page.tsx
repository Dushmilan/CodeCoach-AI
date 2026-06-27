'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AdminStats {
  users?: { total: number; active: number; admin: number; inactive: number };
  questions?: { total: number; by_difficulty: Record<string, number> };
  courses?: { total: number; modules: number; lessons: number };
  system?: { uptime: string; version: string };
  generation?: { total_jobs: number; pending: number; completed: number };
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const res = await fetch('/api/admin/stats', {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Failed to fetch stats');
        const data = await res.json();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading stats');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Welcome back, {user?.username} ({user?.role})
        </p>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-2">{error}</div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Users
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.users?.total ?? 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.users?.active ?? 0} active, {stats.users?.admin ?? 0} admins
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Questions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.questions?.total ?? 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.questions?.by_difficulty
                    ? Object.entries(stats.questions.by_difficulty).map(([d, c]) => (
                        <span key={d} className="mr-2">
                          {d}: {c}
                        </span>
                      ))
                    : 'No data'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Courses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.courses?.total ?? 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.courses?.modules ?? 0} modules, {stats.courses?.lessons ?? 0} lessons
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Generation Jobs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats.generation?.total_jobs ?? 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.generation?.pending ?? 0} pending, {stats.generation?.completed ?? 0}{' '}
                  completed
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <a
                href="/admin/users"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold">
                  U
                </div>
                <div>
                  <div className="text-sm font-medium">Users</div>
                  <div className="text-xs text-muted-foreground">Manage accounts</div>
                </div>
              </a>
              <a
                href="/admin/questions"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center text-green-500 font-bold">
                  Q
                </div>
                <div>
                  <div className="text-sm font-medium">Questions</div>
                  <div className="text-xs text-muted-foreground">Review & import</div>
                </div>
              </a>
              <a
                href="/admin/curriculum"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500 font-bold">
                  C
                </div>
                <div>
                  <div className="text-sm font-medium">Curriculum</div>
                  <div className="text-xs text-muted-foreground">Manage courses</div>
                </div>
              </a>
              <a
                href="/admin/settings"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center text-orange-500 font-bold">
                  S
                </div>
                <div>
                  <div className="text-sm font-medium">Settings</div>
                  <div className="text-xs text-muted-foreground">System config</div>
                </div>
              </a>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
