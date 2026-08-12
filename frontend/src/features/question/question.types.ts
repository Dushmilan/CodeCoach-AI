import { Question, QuestionSummary } from '@/types';

export type QuestionSortKey = 'daily' | 'title' | 'difficulty' | 'category' | 'status';

export interface QuestionFilters {
  difficulty?: 'easy' | 'medium' | 'hard';
  category?: string;
  company?: string;
  status?: 'solved' | 'attempted' | 'not_started';
  search?: string;
  sort?: QuestionSortKey;
}

export interface QuestionState {
  questions: QuestionSummary[];
  allQuestions: QuestionSummary[];
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
