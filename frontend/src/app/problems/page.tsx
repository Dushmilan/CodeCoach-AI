"use client";

import { Header } from "@/components/header/Header";
import { useQuestion } from "@/features/question/question.hook";
import { useLocalStorage } from "@/hooks";
import { getDailySeed, seededShuffle } from "@/lib/shuffle";
import { cn } from "@/lib/utils";
import { QuestionSummary } from "@/types";
import { CheckCircle, Circle, Loader2, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo } from "react";

const difficultyStyles: Record<string, string> = {
  easy: "text-green-400 bg-green-500/10",
  medium: "text-yellow-400 bg-yellow-500/10",
  hard: "text-red-400 bg-red-500/10",
};

export default function ProblemsPage() {
  const router = useRouter();
  const { allQuestions, loadQuestions, isLoading, error } = useQuestion();
  const [progress] = useLocalStorage<Record<string, "attempted" | "solved">>(
    "user_progress",
    {},
  );

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const shuffled = useMemo(() => {
    if (!Array.isArray(allQuestions) || allQuestions.length === 0) return [];
    return seededShuffle(allQuestions, getDailySeed());
  }, [allQuestions]);

  const handleSelect = useCallback(
    (q: QuestionSummary) => {
      router.push(`/problems/${q.id}`);
    },
    [router],
  );

  if (isLoading) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground/40" />
            <span className="text-sm text-muted-foreground/60">
              Loading questions...
            </span>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="flex items-center justify-center min-h-[60vh]">
          <div className="text-sm text-red-400/80 bg-red-500/5 px-4 py-3 rounded-2xl ring-1 ring-red-500/10">
            {error}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />
      <main className="max-w-4xl mx-auto px-6 pt-20 pb-32">
        <div className="flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5">
          <div className="flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5">
              <h1 className="text-lg font-semibold tracking-tight">Problems</h1>
              <p className="text-xs text-muted-foreground/60 mt-0.5">
                {shuffled.length} questions available
              </p>
            </div>

            {shuffled.length === 0 ? (
              <div className="flex items-center justify-center py-16">
                <p className="text-sm text-muted-foreground/40">
                  No questions available yet.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="text-left px-6 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-12">
                        Status
                      </th>
                      <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase">
                        Title
                      </th>
                      <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-24">
                        Difficulty
                      </th>
                      <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-32">
                        Category
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {shuffled.map((q) => {
                      const status = progress[q.id];
                      return (
                        <tr
                          key={q.id}
                          onClick={() => handleSelect(q)}
                          className="border-b border-white/[0.02] hover:bg-white/[0.03] cursor-pointer transition-colors last:border-b-0"
                        >
                          <td className="px-6 py-3.5">
                            {status === "solved" ? (
                              <CheckCircle className="h-4 w-4 text-green-400" />
                            ) : status === "attempted" ? (
                              <XCircle className="h-4 w-4 text-yellow-400" />
                            ) : (
                              <Circle className="h-4 w-4 text-muted-foreground/30" />
                            )}
                          </td>
                          <td className="px-4 py-3.5 font-medium text-foreground/80">
                            {q.title}
                          </td>
                          <td className="px-4 py-3.5">
                            <span
                              className={cn(
                                "text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide",
                                difficultyStyles[q.difficulty],
                              )}
                            >
                              {q.difficulty}
                            </span>
                          </td>
                          <td className="px-4 py-3.5 text-[11px] text-muted-foreground/60">
                            {q.category}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="px-6 py-3 border-t border-white/5 text-[10px] text-muted-foreground/40">
              Randomized daily order &middot; Click any problem to start coding
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
