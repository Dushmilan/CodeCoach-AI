import { Language } from "@/types";

export type DebriefPhase = "idle" | "mission-complete" | "dialogue" | "report";

export interface DebriefContext {
  problem: string;
  code: string;
  language: Language;
}

export interface DebriefExchangeInput {
  question: string;
  answer: string;
}

export interface DebriefExchangeFeedback extends DebriefExchangeInput {
  strengths: string[];
  improvements: string[];
  strongerAnswer: string[];
}

export interface DebriefReport {
  summary: string;
  exchanges: DebriefExchangeFeedback[];
  takeaway: string;
}

export interface DebriefFeature {
  phase: DebriefPhase;
  context: DebriefContext | null;
  currentQuestion: string;
  isTyping: boolean;
  reportLoading: boolean;
  round: number;
  totalRounds: number;
  isLastRound: boolean;
  report: DebriefReport | null;
  openMissionComplete: (context: DebriefContext) => void;
  startDebrief: () => Promise<void>;
  submitExplanation: (text: string) => Promise<void>;
  submitNotSure: () => Promise<void>;
  finishDebrief: () => Promise<void>;
  closeDebrief: () => void;
}
