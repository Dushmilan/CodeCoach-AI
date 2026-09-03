'use client';

import { useEffect } from 'react';
import { useAuth } from '@/providers';
import { coachingService } from './coaching.service';

export function useCoachWarm(questionId: string | null) {
  const { isAuthenticated, isHydrated } = useAuth();

  useEffect(() => {
    if (!questionId || !isAuthenticated || !isHydrated) return;
    const ctrl = new AbortController();
    // Fire-and-forget: never toast, degrade open on 429/abort.
    void coachingService
      .warmContext(questionId, ctrl.signal)
      .catch(() => undefined);
    return () => ctrl.abort();
  }, [questionId, isAuthenticated, isHydrated]);
}
