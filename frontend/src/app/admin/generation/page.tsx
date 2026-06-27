'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface GenJob {
  id: string;
  topic?: string;
  difficulty?: string;
  status: string;
  created_at?: string;
  model?: string;
}

export default function GenerationPage() {
  const { user, token } = useAuth();
  const [jobs, setJobs] = useState<GenJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [triggerForm, setTriggerForm] = useState({
    topic: '',
    difficulty: 'medium',
    count: 5,
    model: '',
  });

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/generation/jobs', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      setJobs((await res.json()).jobs || []);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const triggerGen = async () => {
    setTriggering(true);
    try {
      const body: any = {};
      if (triggerForm.topic) body.topic = triggerForm.topic;
      if (triggerForm.difficulty) body.difficulty = triggerForm.difficulty;
      body.count = triggerForm.count;
      if (triggerForm.model) body.model = triggerForm.model;
      const res = await fetch('/api/admin/generation/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      if (res.ok) fetchJobs();
    } catch {
      /* */
    } finally {
      setTriggering(false);
    }
  };

  const statusBadge = (s: string) => {
    const map: Record<string, { color: string; icon: any }> = {
      pending: { color: 'bg-yellow-500/20 text-yellow-500', icon: Clock },
      running: { color: 'bg-blue-500/20 text-blue-500', icon: Loader2 },
      completed: { color: 'bg-green-500/20 text-green-500', icon: CheckCircle },
      failed: { color: 'bg-red-500/20 text-red-500', icon: XCircle },
    };
    const m = map[s] || map.pending;
    const Icon = m.icon;
    return (
      <span
        className={`text-xs px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${m.color}`}
      >
        <Icon className="h-3 w-3" /> {s}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Question Generation</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Trigger and monitor AI-powered question generation
        </p>
      </div>

      {/* Trigger Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Generate Questions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Topic (optional)</label>
              <input
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                placeholder="e.g. arrays"
                value={triggerForm.topic}
                onChange={(e) => setTriggerForm((f) => ({ ...f, topic: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Difficulty</label>
              <select
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                value={triggerForm.difficulty}
                onChange={(e) => setTriggerForm((f) => ({ ...f, difficulty: e.target.value }))}
              >
                <option value="">Any</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Count</label>
              <input
                type="number"
                min={1}
                max={20}
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                value={triggerForm.count}
                onChange={(e) => setTriggerForm((f) => ({ ...f, count: Number(e.target.value) }))}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Model (optional)</label>
              <input
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                placeholder="gemini-2.5-flash"
                value={triggerForm.model}
                onChange={(e) => setTriggerForm((f) => ({ ...f, model: e.target.value }))}
              />
            </div>
          </div>
          <Button onClick={triggerGen} disabled={triggering}>
            {triggering ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" /> Generating...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-1" /> Trigger Generation
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Jobs List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Generation Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No generation jobs yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground text-xs uppercase">
                    <th className="text-left pb-3 font-medium">ID</th>
                    <th className="text-left pb-3 font-medium">Topic</th>
                    <th className="text-left pb-3 font-medium">Difficulty</th>
                    <th className="text-left pb-3 font-medium">Model</th>
                    <th className="text-left pb-3 font-medium">Status</th>
                    <th className="text-left pb-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => (
                    <tr key={j.id} className="border-b border-border/50">
                      <td className="py-2 text-xs font-mono text-muted-foreground">
                        {j.id.slice(0, 8)}...
                      </td>
                      <td className="py-2">{j.topic || '-'}</td>
                      <td className="py-2">{j.difficulty || '-'}</td>
                      <td className="py-2 text-xs text-muted-foreground">{j.model || 'default'}</td>
                      <td className="py-2">{statusBadge(j.status)}</td>
                      <td className="py-2 text-xs text-muted-foreground">
                        {j.created_at ? new Date(j.created_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
