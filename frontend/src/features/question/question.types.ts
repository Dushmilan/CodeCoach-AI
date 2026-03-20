import { Question, QuestionSummary } from '@/types';

export interface QuestionFilters {
  difficulty?: 'easy' | 'medium' | 'hard';
  category?: string;
  status?: 'solved' | 'attempted' | 'not_started';
}

export interface QuestionState {
  questions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  fullQuestion: Question | null;
  isLoading: boolean;
  isLoadingQuestion: boolean;
  error: string | null;
  filters: QuestionFilters;
}

export interface QuestionActions {
  loadQuestions: () => Promise<void>;
  selectQuestion: (question: QuestionSummary) => Promise<void>;
  setFilters: (filters: QuestionFilters) => void;
  clearError: () => void;
}

export type QuestionFeature = QuestionState & QuestionActions;
