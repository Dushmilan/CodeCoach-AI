'use client';

import { useState, useCallback, useMemo } from 'react';
import { Question, QuestionSummary } from '@/types';
import { questionService } from './question.service';
import { QuestionFilters } from './question.types';
import { showToast } from '@/components/ui/Toast';

interface UseQuestionOptions {
  initialFilters?: QuestionFilters;
}

interface UseQuestionReturn {
  questions: QuestionSummary[];
  allQuestions: QuestionSummary[];
  selectedQuestion: QuestionSummary | null;
  fullQuestion: Question | null;
  isLoading: boolean;
  isLoadingQuestion: boolean;
  error: string | null;
  filters: QuestionFilters;
  loadQuestions: () => Promise<void>;
  selectQuestion: (question: QuestionSummary) => Promise<void>;
  setFilters: (filters: QuestionFilters) => void;
  clearError: () => void;
}

const PAGE_SIZE = 20;

export function useQuestion(options: UseQuestionOptions = {}): UseQuestionReturn & {
  visibleCount: number;
  hasMore: boolean;
  loadMore: () => void;
} {
  const { initialFilters = {} } = options;

  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionSummary | null>(null);
  const [fullQuestion, setFullQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<QuestionFilters>(initialFilters);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await questionService.getQuestions();
      setQuestions(data);
      setVisibleCount(PAGE_SIZE);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load questions';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      console.error('Failed to load questions:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const selectQuestion = useCallback(async (question: QuestionSummary) => {
    setIsLoadingQuestion(true);
    setError(null);
    setSelectedQuestion(question);
    try {
      const data = await questionService.getQuestion(question.id);
      setFullQuestion(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load question details';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      console.error('Failed to load question details:', err);
    } finally {
      setIsLoadingQuestion(false);
    }
  }, []);

  const setFilters = useCallback((newFilters: QuestionFilters) => {
    setFiltersState(newFilters);
    setVisibleCount(PAGE_SIZE);
  }, []);

  const loadMore = useCallback(() => {
    setVisibleCount((c) => c + PAGE_SIZE);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const filteredQuestions = useMemo(() => {
    const query = (filters.search ?? '').trim().toLowerCase();
    return questions.filter((q) => {
      if (filters.difficulty && q.difficulty !== filters.difficulty) return false;
      if (filters.category && q.category !== filters.category) return false;
      if (filters.company && !q.company_tags?.includes(filters.company)) return false;
      if (filters.status && filters.status !== 'not_started') {
        if ((filters.status === 'solved') !== Boolean(q.solved)) return false;
      }
      if (filters.status === 'not_started' && q.solved) return false;
      if (query) {
        const haystack = [q.title, q.category, ...(q.company_tags ?? [])].join(' ').toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      return true;
    });
  }, [questions, filters]);

  const sortedQuestions = useMemo(() => {
    const sort = filters.sort ?? 'daily';
    const items = [...filteredQuestions];
    if (sort === 'title') {
      items.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sort === 'difficulty') {
      const rank = { easy: 0, medium: 1, hard: 2 } as const;
      items.sort(
        (a, b) => rank[a.difficulty] - rank[b.difficulty] || a.title.localeCompare(b.title),
      );
    } else if (sort === 'category') {
      items.sort((a, b) => a.category.localeCompare(b.category) || a.title.localeCompare(b.title));
    } else if (sort === 'status') {
      const statusRank = (q: QuestionSummary) => (q.solved ? 0 : 1);
      items.sort((a, b) => statusRank(a) - statusRank(b) || a.title.localeCompare(b.title));
    }
    return items;
  }, [filteredQuestions, filters.sort]);

  const hasMore = sortedQuestions.length > visibleCount;
  const paginatedQuestions = useMemo(
    () => sortedQuestions.slice(0, visibleCount),
    [sortedQuestions, visibleCount],
  );

  return {
    questions: paginatedQuestions,
    allQuestions: questions,
    selectedQuestion,
    fullQuestion,
    isLoading,
    isLoadingQuestion,
    error,
    filters,
    loadQuestions,
    selectQuestion,
    setFilters,
    clearError,
    visibleCount,
    hasMore,
    loadMore,
  };
}
