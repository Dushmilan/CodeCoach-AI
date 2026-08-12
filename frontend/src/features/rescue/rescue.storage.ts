import { RESCUE_STORAGE_KEY } from "./rescue.config";
import { AbandonedProblem } from "./rescue.types";

export function getAbandonedProblems(): AbandonedProblem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(RESCUE_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveAbandonedProblem(problem: AbandonedProblem): void {
  if (typeof window === "undefined") return;
  try {
    const current = getAbandonedProblems();
    const withoutDuplicate = current.filter(
      (p) => p.questionId !== problem.questionId,
    );
    window.localStorage.setItem(
      RESCUE_STORAGE_KEY,
      JSON.stringify([problem, ...withoutDuplicate]),
    );
  } catch {
    // localStorage unavailable — silently ignore
  }
}

export function removeAbandonedProblem(questionId: string): void {
  if (typeof window === "undefined") return;
  try {
    const current = getAbandonedProblems();
    window.localStorage.setItem(
      RESCUE_STORAGE_KEY,
      JSON.stringify(current.filter((p) => p.questionId !== questionId)),
    );
  } catch {
    // localStorage unavailable — silently ignore
  }
}
