'use client';
import { useMemo } from 'react';
import { Skeleton } from '@/components/ui/Skeleton';
import { useSkillGraph } from './use-skill-graph.hook';
import { BookOpen, RefreshCw, Sparkles } from 'lucide-react';
import { SkillSummary } from '@/types';
const STATUS_COLOR: Record<string, string> = {
  new: '#6b7280',
  learning: '#f59e0b',
  developing: '#3b82f6',
  strong: '#10b981',
  needs_review: '#ef4444',
};
const STATUS_BG: Record<string, string> = {
  new: 'rgba(107,114,128,0.12)',
  learning: 'rgba(245,158,11,0.14)',
  developing: 'rgba(59,130,246,0.14)',
  strong: 'rgba(16,185,129,0.14)',
  needs_review: 'rgba(239,68,68,0.14)',
};
type Pos = { x: number; y: number; depth: number };
function computeLayout(skills: SkillSummary[], edges: { source: string; target: string }[]): Map<string, Pos> {
  const bySlug = new Map(skills.map((s) => [s.skill_slug, s]));
  const prereqMap = new Map<string, string[]>();
  edges.forEach((e) => {
    if (!bySlug.has(e.source) || !bySlug.has(e.target)) return;
    if (!prereqMap.has(e.target)) prereqMap.set(e.target, []);
    prereqMap.get(e.target)!.push(e.source);
  });
  const depthCache = new Map<string, number>();
  const visiting = new Set<string>();
  const depthOf = (slug: string): number => {
    if (depthCache.has(slug)) return depthCache.get(slug)!;
    if (visiting.has(slug)) return 0;
    visiting.add(slug);
    const prereqs = prereqMap.get(slug) ?? [];
    const d = prereqs.length === 0 ? 0 : 1 + Math.max(...prereqs.map(depthOf));
    visiting.delete(slug);
    depthCache.set(slug, d);
    return d;
  };
  skills.forEach((s) => depthOf(s.skill_slug));
  const levels = new Map<number, string[]>();
  depthCache.forEach((d, slug) => {
    if (!levels.has(d)) levels.set(d, []);
    levels.get(d)!.push(slug);
  });
  const width = 900;
  const padX = 80;
  const usableW = width - padX * 2;
  const layerH = 110;
  const pos = new Map<string, Pos>();
  levels.forEach((slugs, depth) => {
    slugs.sort();
    const n = slugs.length;
    slugs.forEach((slug, idx) => {
      const x = n === 1 ? width / 2 : padX + (idx / (n - 1)) * usableW;
      const y = 60 + depth * layerH;
      pos.set(slug, { x, y, depth });
    });
  });
  return pos;
}
export function SkillGraph() {
  const { graph, isLoading, error, refresh, syncFromSubmissions } = useSkillGraph(true);
  const skills = graph?.skills ?? [];
  const edges = graph?.edges ?? [];
  const isBoilerplate = skills.length > 0 && skills.every((s) => s.mastery_score === 0 && s.evidence_count === 0);
  const layout = useMemo(() => (skills.length ? computeLayout(skills, edges) : null), [graph]);
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
        <button onClick={refresh} className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground/80 hover:bg-white/[0.08] transition-colors">
          <RefreshCw className="h-3 w-3" /> Retry
        </button>
      </section>
    );
  }
  if (skills.length === 0 || !layout) {
    return (
      <section aria-label="Skill graph" className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6">
        <p className="text-xs text-muted-foreground/60">No skills yet — solve a problem to build your graph.</p>
      </section>
    );
  }
  const height = 60 + (Math.max(...Array.from(layout.values()).map((p) => p.depth)) + 1) * 110 + 40;
  return (
    <section aria-label="Skill graph" className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6" data-testid="skill-graph">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary/80 ring-1 ring-primary/20">
            <BookOpen className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Your Skill Graph</h2>
            <p className="text-[11px] text-muted-foreground/60">{isBoilerplate ? 'Start solving — this is your starter map' : `${skills.length} skills • ${edges.length} prerequisite links`}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!isBoilerplate && (
            <button onClick={syncFromSubmissions} title="Rebuild graph from completed submissions (DB query)" className="inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground/80 hover:bg-white/[0.08] transition-colors">
              <RefreshCw className="h-3 w-3" /> Sync from history
            </button>
          )}
          <div className="hidden md:flex items-center gap-2 text-[10px]">
            {Object.entries(STATUS_COLOR).map(([k, c]) => (
              <span key={k} className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full" style={{ background: c }} />
                {k.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      </div>
      {isBoilerplate && (
        <div className="mb-4 rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-3">
          <p className="text-xs text-muted-foreground/70">This is a <span className="text-foreground/90 font-medium">boilerplate graph</span> showing every skill in the taxonomy. Solve your first question and we&apos;ll sync your progress — mastery, confidence and prerequisites will light up.</p>
        </div>
      )}
      <div className="overflow-x-auto">
        <svg width={900} height={height} viewBox={`0 0 900 ${height}`} className="min-w-[700px] w-full" role="img" aria-label="Skill prerequisite graph">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX={8} refY={5} markerWidth={6} markerHeight={6} orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,0.25)" />
            </marker>
          </defs>
          {edges.map((e, idx) => {
            const a = layout.get(e.source);
            const b = layout.get(e.target);
            if (!a || !b) return null;
            return <line key={`${e.source}-${e.target}-${idx}`} x1={a.x} y1={a.y + 22} x2={b.x} y2={b.y - 22} stroke="rgba(255,255,255,0.14)" strokeWidth={1.2} markerEnd="url(#arrow)" data-testid="skill-graph-edge" />;
          })}
          {skills.map((s) => {
            const p = layout.get(s.skill_slug);
            if (!p) return null;
            const color = STATUS_COLOR[s.status] ?? STATUS_COLOR.new;
            const bg = STATUS_BG[s.status] ?? STATUS_BG.new;
            const r = 22 + Math.round(s.mastery_score * 10);
            return (
              <g key={s.skill_slug} data-testid="skill-graph-node" data-skill={s.skill_slug} data-status={s.status}>
                <circle cx={p.x} cy={p.y} r={r} fill={bg} stroke={color} strokeWidth={1.6} />
                <circle cx={p.x} cy={p.y} r={Math.max(3, Math.round(s.mastery_score * r))} fill={color} opacity={0.22} />
                <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize={8} fontWeight={700} fill="white" opacity={0.9}>{Math.round(s.mastery_score * 100)}</text>
                <text x={p.x} y={p.y + r + 14} textAnchor="middle" fontSize={10} fontWeight={600} fill="white" opacity={0.85}>{s.name.length > 18 ? s.name.slice(0, 18) + '…' : s.name}</text>
                <text x={p.x} y={p.y + r + 26} textAnchor="middle" fontSize={8} fill="white" opacity={0.45}>{s.status.replace('_', ' ')}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <p className="text-[11px] text-muted-foreground/40 mt-3">Node size = mastery · color = status · arrows = prerequisite. Initial boilerplate shows all 22 skills at 0% (gray); your solves fill it in.</p>
    </section>
  );
}
