'use client';

import Link from 'next/link';
import { ArrowRight, Lightbulb, LogIn, RotateCcw, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAuth } from '@/providers';
import { RecommendedQuestion } from '@/types';
import { useRecommendedQuestions } from './use-recommended-questions.hook';

export function RecommendedQuestions() {
  const { isHydrated, isAuthenticated } = useAuth();
  const { recommendations, isLoading, error, refresh } =
    useRecommendedQuestions();

  if (!isHydrated) return null;

  return (
    <section aria-label="Practice next" className="pb-6">
      <div className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-5 md:p-6">
        <div className="flex items-center gap-2.5 mb-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary/80 ring-1 ring-primary/20">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Practice next</h2>
            <p className="text-[11px] text-muted-foreground/60">
              Personalized picks based on your progress
            </p>
          </div>
        </div>

        {!isAuthenticated ? (
          <AnonymousState />
        ) : isLoading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} onRetry={refresh} />
        ) : recommendations.length === 0 ? (
          <EmptyState />
        ) : (
          <CardGrid recommendations={recommendations} />
        )}
      </div>
    </section>
  );
}

function AnonymousState() {
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <p className="text-xs text-muted-foreground/60">
        Sign in to get personalized practice recommendations.
      </p>
      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 ring-1 ring-primary/20 px-4 py-2 text-xs font-medium text-primary/90 hover:bg-primary/20 transition-colors"
      >
        <LogIn className="h-3.5 w-3.5" />
        Sign in
      </Link>
    </div>
  );
}

function LoadingState() {
  return (
    <div
      data-testid="recommendations-loading"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
      aria-busy="true"
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="rounded-2xl border border-white/[0.04] bg-white/[0.01] p-4"
        >
          <div className="flex items-center justify-between gap-2">
            <Skeleton width={120} height={14} />
            <Skeleton width={40} height={14} />
          </div>
          <Skeleton width={80} height={12} className="mt-3" />
          <Skeleton width="100%" height={12} className="mt-3" />
        </div>
      ))}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <p className="text-xs text-red-400/80">{message}</p>
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-3 py-1.5 text-xs font-medium text-muted-foreground/80 hover:bg-white/[0.08] transition-colors"
      >
        <RotateCcw className="h-3 w-3" />
        Retry
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <p className="text-xs text-muted-foreground/60">
      No recommendations yet. Solve a few problems to unlock personalized
      practice.
    </p>
  );
}

function CardGrid({ recommendations }: { recommendations: RecommendedQuestion[] }) {
  return (
    <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {recommendations.map((rec) => (
        <li key={rec.question.id}>
          <Link
            href={`/problems/${rec.question.id}`}
            className="group flex h-full flex-col rounded-2xl border border-white/[0.04] bg-white/[0.01] p-4 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:border-white/[0.10] hover:bg-white/[0.04]"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-foreground/90 group-hover:text-foreground transition-colors">
                {rec.question.title}
              </span>
              <Badge variant={rec.question.difficulty} size="sm">
                {rec.question.difficulty}
              </Badge>
            </div>
            <div className="mt-1.5 flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] text-muted-foreground/60">
                {rec.question.category}
              </span>
              <Badge variant="outline" size="sm">
                {rec.skill_name}
              </Badge>
            </div>
            <div className="mt-3 flex items-start gap-2">
              <Lightbulb className="h-3.5 w-3.5 text-primary/60 mt-0.5 shrink-0" />
              <p className="text-[11px] leading-relaxed text-muted-foreground/70">
                {rec.reason_text}
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1 pt-3 text-[11px] font-medium text-primary/80 group-hover:text-primary transition-colors">
              Practice
              <ArrowRight className="h-3 w-3 transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-0.5" />
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
