import { StructuredCoachingResponse, ChatMessage } from '@/types';

export type CoachingMode = 'hint' | 'review' | 'explain' | 'debug' | 'freeform';

export interface CoachingRequest {
  problem: string;
  language: string;
  code: string;
  message: string;
  mode: CoachingMode;
  difficulty?: string;
}

export interface CoachingResponse {
  response: string;
  structured: StructuredCoachingResponse | null;
}

export interface CoachingState {
  messages: ChatMessage[];
  isTyping: boolean;
  error: string | null;
}

export interface CoachingActions {
  sendMessage: (message: string, mode: CoachingMode, problem: string, code: string, language: string) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

export type CoachingFeature = CoachingState & CoachingActions;
