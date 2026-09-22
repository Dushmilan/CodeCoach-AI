'use client';

import { useCallback, useEffect, useState } from 'react';
import { SkillGraphResponse } from '@/types';
import { skillGraphService } from './skill-graph.service';
import { QUESTION_SOLVED_EVENT } from '@/lib/solved-event';

export function useSkillGraph(includeBoilerplate = true) {
  const [graph, setGraph] = useState<SkillGraphResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await skillGraphService.getGraph(includeBoilerplate);
      setGraph(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load skill graph');
    } finally {
      setIsLoading(false);
    }
  }, [includeBoilerplate]);

  const syncFromSubmissions = useCallback(async () => {
    try {
      await skillGraphService.syncFromSubmissions();
      await fetchGraph();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sync failed');
    }
  }, [fetchGraph]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Refresh after a solve so skill levels reflect the new submission (#277).
  useEffect(() => {
    const handler = () => {
      void fetchGraph();
    };
    if (typeof window !== "undefined") {
      window.addEventListener(QUESTION_SOLVED_EVENT, handler);
      return () => window.removeEventListener(QUESTION_SOLVED_EVENT, handler);
    }
  }, [fetchGraph]);

  return { graph, isLoading, error, refresh: fetchGraph, syncFromSubmissions };
}
