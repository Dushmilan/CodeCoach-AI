import { StructuredCoachingResponse, ChatMessage } from "@/types";

export type CoachingMode =
  | "hint"
  | "review"
  | "explain"
  | "debug"
  | "freeform"
  | "animate";

export interface CoachingRequest {
  problem: string;
  language: string;
  code: string;
  message: string;
  mode: CoachingMode;
  difficulty?: string;
  initial_code?: string;
  question_id?: string;
}

export interface CoachingResponse {
  response: string;
  structured: StructuredCoachingResponse | null;
}

export interface CoachingState {
  messages: ChatMessage[];
  isTyping: boolean;
  error: string | null;
  limitReached: boolean;
}

export interface CoachingActions {
  sendMessage: (
    message: string,
    mode: CoachingMode,
    problem: string,
    code: string,
    language: string,
    lessonContext?: string,
    difficulty?: string,
    initialCode?: string,
    questionId?: string,
  ) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
  clearLimitReached: () => void;
  hydrateMessages?: (msgs: ChatMessage[]) => void;
}

export type CoachingFeature = CoachingState & CoachingActions;
