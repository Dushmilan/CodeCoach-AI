'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '@/providers';
import { RecommendedQuestion } from '@/types';
import { skillGraphService } from './skill-graph.service';

interface UseRecommendedQuestionsReturn {
  recommendations: RecommendedQuestion[];
  isLoading: boolean;
  error: string | null;
  loadRecommendations: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function useRecommendedQuestions(): UseRecommendedQuestionsReturn {
  const { isAuthenticated, isHydrated } = useAuth();
  const [recommendations, setRecommendations] = useState<RecommendedQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const didAutoLoad = useRef(false);
  const active = useRef(true);

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);

  const loadRecommendations = useCallback(async () => {
    if (!isAuthenticated || !isHydrated) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await skillGraphService.getRecommendedQuestions();
      if (active.current) {
        setRecommendations(data);
      }
    } catch (err) {
      if (active.current) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load recommendations',
        );
      }
    } finally {
      if (active.current) {
        setIsLoading(false);
      }
    }
  }, [isAuthenticated, isHydrated]);

  useEffect(() => {
    if (!isAuthenticated) {
      didAutoLoad.current = false;
      return;
    }
    if (isHydrated && !didAutoLoad.current) {
      didAutoLoad.current = true;
      void loadRecommendations();
    }
  }, [isAuthenticated, isHydrated, loadRecommendations]);

  const refresh = useCallback(() => loadRecommendations(), [loadRecommendations]);

  return {
    recommendations,
    isLoading,
    error,
    loadRecommendations,
    refresh,
  };
}
