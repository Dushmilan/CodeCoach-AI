"use client";

import type { SubmitResponse } from "@/features/code-execution/code-execution.types";

/** Dispatched on a full-pass solve so Continue / graphs / What's-next refresh. */
export const QUESTION_SOLVED_EVENT = "question-solved";

/** Kept for existing listeners (e.g. recommendations hook). */
export const LEARNER_CONTEXT_INVALIDATED_EVENT = "learner-context-invalidated";

export interface QuestionSolvedDetail {
  questionId: string;
}

export function isFullPass(result: SubmitResponse | null | undefined): result is SubmitResponse {
  return !!result && result.passed_count === result.total;
}

/** Notify solved-event listeners; safe to call during SSR (no-op). */
export function dispatchSolvedEvents(questionId: string): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent<QuestionSolvedDetail>(QUESTION_SOLVED_EVENT, {
      detail: { questionId },
    }),
  );
  window.dispatchEvent(new Event(LEARNER_CONTEXT_INVALIDATED_EVENT));
}
