import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useRecommendedQuestions } from './use-recommended-questions.hook';
import { RecommendedQuestion } from '@/types';

const { mockGetRecommendedQuestions } = vi.hoisted(() => ({
  mockGetRecommendedQuestions: vi.fn(),
}));

vi.mock('./skill-graph.service', () => ({
  skillGraphService: {
    getRecommendedQuestions: (...args: unknown[]) =>
      mockGetRecommendedQuestions(...args),
  },
}));

const { mockUseAuth } = vi.hoisted(() => ({
  mockUseAuth: vi.fn(),
}));

vi.mock('@/providers', () => ({
  useAuth: () => mockUseAuth(),
}));

const sampleRecommendation: RecommendedQuestion = {
  skill_slug: 'arrays',
  skill_name: 'Arrays',
  reason: 'weak_skill',
  reason_text: 'Arrays needs practice to become a strength.',
  question: {
    id: 'two-sum',
    title: 'Two Sum',
    difficulty: 'easy',
    category: 'arrays',
    company_tags: ['Google'],
    description: 'Find two numbers that add up to target',
    starter: {
      python: 'def two_sum(nums, target):',
      javascript: 'function twoSum(nums, target) {}',
      java: 'class Solution {}',
      cpp: '',
      c: '',
      go: '',
      rust: '',
      typescript: '',
    },
    examples: [{ input: '[2,7,11,15], 9', output: '[0,1]' }],
    test_cases: [{ input: '[2,7], 9', expected_output: '[0,1]' }],
    hints: ['Use a hash map'],
    solution: 'def two_sum(nums, target): return [0, 1]',
    time_complexity: 'O(n)',
    space_complexity: 'O(n)',
  },
};

function mockAuth(overrides: Partial<{ isAuthenticated: boolean; isHydrated: boolean }> = {}) {
  mockUseAuth.mockReturnValue({
    isAuthenticated: overrides.isAuthenticated ?? true,
    isHydrated: overrides.isHydrated ?? true,
  });
}

beforeEach(() => {
  mockGetRecommendedQuestions.mockReset();
  mockUseAuth.mockReset();
  mockAuth();
});

describe('useRecommendedQuestions', () => {
  describe('initial state', () => {
    it('starts with empty recommendations', () => {
      mockAuth({ isAuthenticated: false, isHydrated: false });
      const { result } = renderHook(() => useRecommendedQuestions());
      expect(result.current.recommendations).toEqual([]);
    });

    it('starts not loading and with no error', () => {
      mockAuth({ isAuthenticated: false, isHydrated: false });
      const { result } = renderHook(() => useRecommendedQuestions());
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('anonymous users', () => {
    it('does not call the service when not authenticated', async () => {
      mockAuth({ isAuthenticated: false, isHydrated: true });
      renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).not.toHaveBeenCalled();
      });
    });

    it('does not call the service before hydration', async () => {
      mockAuth({ isAuthenticated: true, isHydrated: false });
      renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).not.toHaveBeenCalled();
      });
    });
  });

  describe('loadRecommendations', () => {
    it('loads recommendations from the service', async () => {
      mockGetRecommendedQuestions.mockResolvedValue([sampleRecommendation]);

      const { result } = renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      });
      mockGetRecommendedQuestions.mockClear();

      await act(async () => {
        await result.current.loadRecommendations();
      });

      expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      expect(result.current.recommendations).toHaveLength(1);
      expect(result.current.recommendations[0].question.id).toBe('two-sum');
    });

    it('sets isLoading to true during load and false after', async () => {
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockGetRecommendedQuestions.mockReturnValue(promise);

      const { result } = renderHook(() => useRecommendedQuestions());

      act(() => {
        void result.current.loadRecommendations();
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolvePromise!([sampleRecommendation]);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('sets error on failure', async () => {
      mockGetRecommendedQuestions.mockRejectedValue(new Error('Network failure'));

      const { result } = renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      });
      mockGetRecommendedQuestions.mockClear();
      mockGetRecommendedQuestions.mockRejectedValue(new Error('Network failure'));

      await act(async () => {
        await result.current.loadRecommendations();
      });

      expect(result.current.error).toBe('Network failure');
      expect(result.current.recommendations).toEqual([]);
    });

    it('handles non-Error rejection with a generic message', async () => {
      mockGetRecommendedQuestions.mockRejectedValue('unknown error');

      const { result } = renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      });
      mockGetRecommendedQuestions.mockClear();
      mockGetRecommendedQuestions.mockRejectedValue('unknown error');

      await act(async () => {
        await result.current.loadRecommendations();
      });

      expect(result.current.error).toBe('Failed to load recommendations');
    });
  });

  describe('auto-load', () => {
    it('auto-loads once when hydrated and authenticated', async () => {
      mockGetRecommendedQuestions.mockResolvedValue([sampleRecommendation]);

      renderHook(() => useRecommendedQuestions());

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      });
    });

    it('auto-loads after hydration completes for an authenticated user', async () => {
      mockAuth({ isAuthenticated: true, isHydrated: false });
      mockGetRecommendedQuestions.mockResolvedValue([sampleRecommendation]);

      const { rerender } = renderHook(() => useRecommendedQuestions());

      mockAuth({ isAuthenticated: true, isHydrated: true });
      rerender();

      await waitFor(() => {
        expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('refresh', () => {
    it('re-fetches recommendations', async () => {
      mockGetRecommendedQuestions.mockResolvedValue([sampleRecommendation]);

      const { result } = renderHook(() => useRecommendedQuestions());

      await act(async () => {
        await result.current.refresh();
      });

      expect(mockGetRecommendedQuestions).toHaveBeenCalledTimes(2);
    });
  });
});
