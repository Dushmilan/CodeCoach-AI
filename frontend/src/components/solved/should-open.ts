export interface SubmitTally {
  passed_count: number;
  total: number;
}

export function shouldOpenSolvedOverlay(
  result: SubmitTally | null | undefined,
  shownForQuestionId: string | null,
  questionId: string,
): boolean {
  if (!result || result.total <= 0) return false;
  if (result.passed_count !== result.total) return false;
  return shownForQuestionId !== questionId;
}
