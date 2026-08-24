"use client";

import { Header } from "@/components/header/Header";
import { MemoryGraph } from "@/features/memory/MemoryGraph";
import { RescueDueQueue } from "@/features/rescue/RescueDueQueue";
import { ReviewsDueQueue } from "@/features/review/ReviewsDueQueue";
import { useQuestion } from "@/features/question/question.hook";
import { useCallback, useEffect } from "react";

export default function StudentDashboardPage() {
  const { allQuestions, loadQuestions } = useQuestion();

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const resolveTitle = useCallback(
    (questionId: string) => allQuestions.find((q) => q.id === questionId)?.title,
    [allQuestions],
  );

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />
      <main className="max-w-5xl mx-auto px-6 pt-20 pb-32">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground/60 mt-1">
            Your memory graph — what to refresh before you forget.
          </p>
        </div>
        <MemoryGraph />
        <RescueDueQueue resolveTitle={resolveTitle} />
        <ReviewsDueQueue resolveTitle={resolveTitle} />
      </main>
    </div>
  );
}
