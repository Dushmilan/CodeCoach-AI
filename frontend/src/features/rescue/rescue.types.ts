export type RescueTier = "none" | "t1" | "t2" | "t3";

export interface RescueCheckpoint {
  id: string;
  label: string;
  state: "passed" | "current" | "upcoming" | "error";
  detail?: string;
}

export interface AbandonedProblem {
  questionId: string;
  title: string;
  stuckCheckpoint: string | null;
  passedCount: number;
  total: number;
  abandonedAt: number;
}
