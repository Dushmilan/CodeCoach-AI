'use client';

import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useSkillGraph } from './use-skill-graph.hook';
import { BookOpen, Sparkles, RefreshCw } from 'lucide-react';

const STATUS_COLOR: Record<string, string> = {
  new: 'bg-white/[0.04] text-muted-foreground/60 ring-white/10',
  learning: 'bg-amber-500/10 text-amber-300 ring-amber-500/20',
  developing: 'bg-blue-500/10 text-blue-300 ring-blue-500/20',
  strong: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20',
  needs_review: 'bg-red-500/10 text-red-300 ring-red-500/20',
};

function masteryLabel(score: number) {
  if (score >= 0.75) return 'Strong';
  if (score >= 0.45) return 'Developing';
  if (score >= 0.2) return 'Learning';
  return 'New';
}

export function SkillGraph() {
  const { graph, isLoading, error, refresh, syncFromSubmissions } = useSkillGraph(true);

  if (isLoading) {
    return (
      <section aria-label="Skill graph" className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6">
        <div className="flex items-center gap-2.5 mb-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary/80 ring-1 ring-primary/20">
            <Sparkles className="h-4 w-4" />
          </span>
          <Skeleton width={140} height={14} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="skill-graph-loading">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-4">
              <Skeleton width={100} height={14} />
              <Skeleton width="100%" height={8} className="mt-3" />
              <Skeleton width={60} height={12} className="mt-3" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section aria-label="Skill graph" className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6">
        <p className="text-xs text-red-400/80">{error}</p>
        <button
          onClick={refresh}
          className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground/80 hover:bg-white/[0.08] transition-colors"
        >
          <RefreshCw className="h-3 w-3" /> Retry
        </button>
      </section>
    );
  }

  const skills = graph?.skills ?? [];
  const edges = graph?.edges ?? [];
  const isBoilerplate = skills.length > 0 && skills.every((s) => s.mastery_score === 0 && s.evidence_count === 0);

  return (
    <section aria-label="Skill graph" className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary/80 ring-1 ring-primary/20">
            <BookOpen className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Your Skill Graph</h2>
            <p className="text-[11px] text-muted-foreground/60">
              {isBoilerplate
                ? 'Start solving — this is your starter map'
                : `${skills.length} skills • ${edges.length} prerequisite links`}
            </p>
          </div>
        </div>
        {!isBoilerplate && (
          <button
            onClick={syncFromSubmissions}
            title="Rebuild graph from completed submissions (DB query)"
            className="inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground/80 hover:bg-white/[0.08] transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> Sync from history
          </button>
        )}
      </div>

      {skills.length === 0 ? (
        <p className="text-xs text-muted-foreground/60">No skills yet — solve a problem to build your graph.</p>
      ) : (
        <>
          {isBoilerplate && (
            <div className="mb-4 rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-3">
              <p className="text-xs text-muted-foreground/70">
                This is a <span className="text-foreground/90 font-medium">boilerplate graph</span> showing every skill in the taxonomy.
                Solve your first question and we&apos;ll sync your progress from the database — mastery, confidence and prerequisites will light up.
              </p>
            </div>
          )}
          <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {skills.map((skill) => (
              <li
                key={skill.skill_slug}
                data-testid="skill-node"
                data-skill={skill.skill_slug}
                className="group flex flex-col rounded-2xl border border-white/[0.04] bg-white/[0.01] p-4 hover:border-white/[0.10] hover:bg-white/[0.04] transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-medium text-foreground/90">{skill.name}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ${STATUS_COLOR[skill.status] ?? STATUS_COLOR.new}`}>
                    {masteryLabel(skill.mastery_score)}
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary/80 transition-all duration-500"
                    style={{ width: `${Math.round(skill.mastery_score * 100)}%` }}
                    aria-label={`${skill.name} mastery ${Math.round(skill.mastery_score * 100)}%`}
                  />
                </div>
                <div className="mt-2 flex items-center justify-between gap-2 text-[11px] text-muted-foreground/60">
                  <span>mastery {(skill.mastery_score * 100).toFixed(0)}% • conf {(skill.confidence * 100).toFixed(0)}%</span>
                  <Badge variant="outline" size="sm">{skill.skill_slug}</Badge>
                </div>
                {skill.evidence_count > 0 && (
                  <p className="mt-1 text-[11px] text-muted-foreground/50">
                    {skill.evidence_count} evidence • {skill.recent_error_count} recent errors
                  </p>
                )}
              </li>
            ))}
          </ul>
          {edges.length > 0 && (
            <p className="mt-4 text-[11px] text-muted-foreground/40">
              {edges.length} prerequisite edges — e.g. <span className="text-muted-foreground/60">{edges[0].source} → {edges[0].target}</span>
            </p>
          )}
        </>
      )}
    </section>
  );
}
