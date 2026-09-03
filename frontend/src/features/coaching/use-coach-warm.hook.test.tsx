'use client';

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useCoachWarm } from './use-coach-warm.hook';

const { mockWarmContext } = vi.hoisted(() => ({
  mockWarmContext: vi.fn(),
}));

vi.mock('./coaching.service', () => ({
  coachingService: {
    warmContext: (...args: unknown[]) => mockWarmContext(...args),
  },
}));

const { mockUseAuth } = vi.hoisted(() => ({
  mockUseAuth: vi.fn(),
}));

vi.mock('@/providers', () => ({
  useAuth: () => mockUseAuth(),
}));

describe('useCoachWarm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWarmContext.mockResolvedValue({ status: 'warming' });
  });

  it('warms once when authenticated with questionId', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isHydrated: true });
    renderHook(({ id }: { id: string | null }) => useCoachWarm(id), {
      initialProps: { id: 'two-sum' },
    });
    await vi.waitFor(() => {
      expect(mockWarmContext).toHaveBeenCalledTimes(1);
    });
    expect(mockWarmContext).toHaveBeenCalledWith(
      'two-sum',
      expect.any(AbortSignal),
    );
  });

  it('does not warm when unauthenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, isHydrated: true });
    renderHook(({ id }: { id: string | null }) => useCoachWarm(id), {
      initialProps: { id: 'two-sum' },
    });
    expect(mockWarmContext).not.toHaveBeenCalled();
  });

  it('degrades silently when warm rejects', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, isHydrated: true });
    mockWarmContext.mockRejectedValueOnce(new Error('429'));
    renderHook(({ id }: { id: string | null }) => useCoachWarm(id), {
      initialProps: { id: 'two-sum' },
    });
    await vi.waitFor(() => {
      expect(mockWarmContext).toHaveBeenCalledTimes(1);
    });
  });
});
