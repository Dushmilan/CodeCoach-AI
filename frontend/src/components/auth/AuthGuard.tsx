'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers';
import { showToast } from '@/components/ui/Toast';

type AuthGuardAction = 'run' | 'submit' | 'coach';

const ACTION_LABELS: Record<AuthGuardAction, string> = {
  run: 'run code',
  submit: 'submit code',
  coach: 'use the AI Coach',
};

export function useAuthGuard() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const requireAuth = useCallback((action: AuthGuardAction): boolean => {
    if (isLoading) return false;
    if (!isAuthenticated) {
      showToast(`Please sign in to ${ACTION_LABELS[action]}`, 'info');
      router.push(`/login?redirect=${encodeURIComponent(window.location.pathname)}&action=${action}`);
      return false;
    }
    return true;
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading, requireAuth, ACTION_LABELS };
}
