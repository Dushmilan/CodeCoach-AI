"use client";

import { Header } from "@/components/header/Header";
import { useQuestion } from "@/features/question/question.hook";
import { resetOnboardingTour } from "@/components/onboarding/OnboardingTour";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/Skeleton";

const SkillGraph = dynamic(
  () => import("@/features/skill-graph/SkillGraph").then((m) => m.SkillGraph),
  {
    ssr: false,
    loading: () => <Skeleton className="h-32 w-full rounded-xl" />,
  },
);
const LearningSignals = dynamic(() => import("@/features/analytics/LearningSignals"), {
  ssr: false,
  loading: () => <Skeleton className="h-24 w-full rounded-xl" />,
});
const MemoryGraph = dynamic(
  () => import("@/features/memory/MemoryGraph").then((m) => m.MemoryGraph),
  {
    ssr: false,
    loading: () => <Skeleton className="h-48 w-full rounded-xl" />,
  },
);
const RescueDueQueue = dynamic(
  () => import("@/features/rescue/RescueDueQueue").then((m) => m.RescueDueQueue),
  {
    ssr: false,
    loading: () => <Skeleton className="h-20 w-full rounded-xl" />,
  },
);
const ReviewsDueQueue = dynamic(
  () => import("@/features/review/ReviewsDueQueue").then((m) => m.ReviewsDueQueue),
  {
    ssr: false,
    loading: () => <Skeleton className="h-20 w-full rounded-xl" />,
  },
);

export default function StudentDashboardPage() {
  const { allQuestions, loadQuestions } = useQuestion();
  const [replayKey, setReplayKey] = useState(0);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const resolveTitle = useCallback(
    (questionId: string) => allQuestions.find((q) => q.id === questionId)?.title,
    [allQuestions],
  );

  const handleReplayTour = useCallback(() => {
    resetOnboardingTour();
    // force remount of tour listeners by bumping key and dispatching storage event
    setReplayKey((k) => k + 1);
    try {
      window.dispatchEvent(new StorageEvent("storage", { key: "onboarding-done", newValue: null }));
    } catch {
      // ignore
    }
    // reload to re-trigger tour mount read (graceful for CS-dept onboarding)
    if (typeof window !== "undefined") window.location.reload();
  }, []);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />
      <main className="max-w-5xl mx-auto px-6 pt-20 pb-32" key={replayKey}>
        <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
            <p className="text-sm text-muted-foreground/60 mt-1">
              Your memory graph — what to refresh before you forget.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/problems"
              className="inline-flex items-center gap-1.5 rounded-full bg-primary/90 text-primary-foreground px-4 py-2 text-xs font-medium hover:bg-primary transition-colors"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Start practicing
            </Link>
            <button
              type="button"
              onClick={handleReplayTour}
              className="inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] ring-1 ring-white/10 px-4 py-2 text-xs font-medium text-muted-foreground hover:bg-white/[0.08] transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Replay tour
            </button>
          </div>
        </div>
        <div className="rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6 space-y-6">
            <SkillGraph />
            <LearningSignals />
            <MemoryGraph />
            <RescueDueQueue resolveTitle={resolveTitle} />
            <ReviewsDueQueue resolveTitle={resolveTitle} />
          </div>
        </div>
      </main>
    </div>
  );
}
