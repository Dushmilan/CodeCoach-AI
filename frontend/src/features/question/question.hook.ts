"use client";

import { useState, useCallback, useMemo } from 'react';
import { Question, QuestionSummary } from '@/types';
import { questionService } from './question.service';
import { QuestionFilters } from './question.types';

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

export function useQuestion(options: UseQuestionOptions = {}): UseQuestionReturn {
  const { initialFilters = {} } = options;

  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionSummary | null>(null);
  const [fullQuestion, setFullQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<QuestionFilters>(initialFilters);

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await questionService.getQuestions();
      setQuestions(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load questions';
      setError(errorMessage);
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
      console.error('Failed to load question details:', err);
    } finally {
      setIsLoadingQuestion(false);
    }
  }, []);

  const setFilters = useCallback((newFilters: QuestionFilters) => {
    setFiltersState(newFilters);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const filteredQuestions = useMemo(() => {
    return questions.filter(q => {
      if (filters.difficulty && q.difficulty !== filters.difficulty) return false;
      if (filters.category && q.category !== filters.category) return false;
      return true;
    });
  }, [questions, filters]);

  return {
    questions: filteredQuestions,
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
  };
}
