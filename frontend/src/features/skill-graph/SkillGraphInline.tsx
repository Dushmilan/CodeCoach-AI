'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Loader2, Sparkles } from 'lucide-react';
import { skillGraphService } from './skill-graph.service';
import { SkillGraphResponse, SkillSummary } from '@/types';

function StatusBadge({ status }: { status: SkillSummary['status'] }) {
  const map: Record<string, string> = {
    new: 'bg-white/[0.04] text-muted-foreground/60 ring-white/5',
    learning: 'bg-amber-500/10 text-amber-400 ring-amber-500/20',
    developing: 'bg-blue-500/10 text-blue-400 ring-blue-500/20',
    strong: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/20',
    needs_review: 'bg-red-500/10 text-red-400 ring-red-500/20',
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ${map[status] ?? map.new}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function MasteryBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
      <div
        className="h-full rounded-full bg-primary transition-all duration-500"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

export function SkillGraphInline({ isAuthenticated }: { isAuthenticated?: boolean }) {
  const [data, setData] = useState<SkillGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = isAuthenticated
          ? await skillGraphService.getGraph(true)
          : await skillGraphService.getBoilerplate();
        if (!cancelled) setData(res);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load skills');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  return (
    <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4" role="region" aria-label="Skill graph">
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/20">
            <BookOpen className="h-3.5 w-3.5 text-primary/80" />
          </span>
          <div>
            <p className="text-xs font-medium text-foreground/80">Your Skills</p>
            <p className="text-[10px] text-muted-foreground/60">
              {isAuthenticated ? 'Personalized mastery map' : 'Preview — sign in to track progress'}
            </p>
          </div>
        </div>
        {data && (
          <span className="text-[10px] text-muted-foreground/50">
            {data.skills.length} skills · {data.edges.length} links
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-6 text-muted-foreground/50" data-testid="skill-graph-loading">
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
          <span className="text-xs">Loading skills…</span>
        </div>
      ) : error ? (
        <div className="rounded-xl bg-red-500/10 ring-1 ring-red-500/20 p-3">
          <p className="text-xs text-red-400/80" data-testid="skill-graph-error">{error}</p>
        </div>
      ) : !data || data.skills.length === 0 ? (
        <p className="text-xs text-muted-foreground/60 text-center py-4">No skills yet.</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1" data-testid="skill-graph-list">
          {data.skills.slice(0, 22).map((s) => (
            <div
              key={s.skill_slug}
              className="rounded-xl bg-white/[0.02] ring-1 ring-white/[0.03] px-3 py-2.5 hover:bg-white/[0.04] transition-colors"
              data-testid="skill-graph-item"
              data-skill={s.skill_slug}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium text-foreground/80 truncate">{s.name}</span>
                <StatusBadge status={s.status} />
              </div>
              <div className="mt-1.5 flex items-center gap-2">
                <MasteryBar value={s.mastery_score} />
                <span className="text-[10px] text-muted-foreground/60 shrink-0">{Math.round(s.mastery_score * 100)}%</span>
              </div>
              {s.evidence_count > 0 && (
                <p className="text-[10px] text-muted-foreground/50 mt-1">
                  {s.evidence_count} evidence · {s.trend}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <Link
          href={isAuthenticated ? '/dashboard' : '/learn'}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-primary/80 hover:text-primary transition-colors"
        >
          <Sparkles className="h-3 w-3" />
          {isAuthenticated ? 'Open dashboard' : 'Start learning'}
        </Link>
        {!isAuthenticated && (
          <span className="text-[10px] text-muted-foreground/40">Sign in to save progress</span>
        )}
      </div>
    </div>
  );
}
