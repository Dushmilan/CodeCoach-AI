import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useQuestion } from './question.hook';
import { QuestionSummary, Question } from '@/types';

const mockGetQuestions = vi.fn();
const mockGetQuestion = vi.fn();

vi.mock('./question.service', () => ({
  questionService: {
    getQuestions: (...args: unknown[]) => mockGetQuestions(...args),
    getQuestion: (...args: unknown[]) => mockGetQuestion(...args),
  },
}));

const sampleQuestions: QuestionSummary[] = [
  { id: '1', title: 'Two Sum', difficulty: 'easy', category: 'arrays', company_tags: ['Google'] },
  { id: '2', title: 'Add Two Numbers', difficulty: 'medium', category: 'linked-list', company_tags: [] },
  { id: '3', title: 'Median of Two Sorted Arrays', difficulty: 'hard', category: 'arrays', company_tags: ['Google', 'Meta'] },
];

const sampleFullQuestion: Question = {
  id: '1',
  title: 'Two Sum',
  difficulty: 'easy',
  category: 'arrays',
  company_tags: ['Google'],
  description: 'Find two numbers that add up to target',
  starter: { python: 'def two_sum(nums, target):', javascript: 'function twoSum(nums, target) {}', java: 'class Solution {}' },
  examples: [{ input: '[2,7,11,15], 9', output: '[0,1]' }],
  test_cases: [{ input: '[2,7], 9', expected_output: '[0,1]' }],
  hints: ['Use a hash map'],
  solution: 'def two_sum(nums, target): return [0, 1]',
  time_complexity: 'O(n)',
  space_complexity: 'O(n)',
};

beforeEach(() => {
  mockGetQuestions.mockReset();
  mockGetQuestion.mockReset();
});

describe('useQuestion', () => {
  describe('initial state', () => {
    it('starts with empty questions', () => {
      const { result } = renderHook(() => useQuestion());
      expect(result.current.questions).toEqual([]);
      expect(result.current.allQuestions).toEqual([]);
    });

    it('starts with no selected question', () => {
      const { result } = renderHook(() => useQuestion());
      expect(result.current.selectedQuestion).toBeNull();
      expect(result.current.fullQuestion).toBeNull();
    });

    it('starts not loading', () => {
      const { result } = renderHook(() => useQuestion());
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isLoadingQuestion).toBe(false);
    });

    it('starts with no error', () => {
      const { result } = renderHook(() => useQuestion());
      expect(result.current.error).toBeNull();
    });
  });

  describe('loadQuestions', () => {
    it('loads questions from service', async () => {
      mockGetQuestions.mockResolvedValue(sampleQuestions);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      expect(mockGetQuestions).toHaveBeenCalledOnce();
      expect(result.current.allQuestions).toHaveLength(3);
      expect(result.current.questions).toHaveLength(3);
    });

    it('sets isLoading to true during load and false after', async () => {
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => { resolvePromise = resolve; });
      mockGetQuestions.mockReturnValue(promise);

      const { result } = renderHook(() => useQuestion());

      act(() => {
        result.current.loadQuestions();
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolvePromise!(sampleQuestions);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('sets error on failure', async () => {
      mockGetQuestions.mockRejectedValue(new Error('Network failure'));

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      expect(result.current.error).toBe('Network failure');
      expect(result.current.allQuestions).toEqual([]);
    });

    it('handles non-Error rejection', async () => {
      mockGetQuestions.mockRejectedValue('unknown error');

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      expect(result.current.error).toBe('Failed to load questions');
    });
  });

  describe('selectQuestion', () => {
    it('loads full question details', async () => {
      mockGetQuestion.mockResolvedValue(sampleFullQuestion);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.selectQuestion(sampleQuestions[0]);
      });

      expect(mockGetQuestion).toHaveBeenCalledWith('1');
      expect(result.current.selectedQuestion?.id).toBe('1');
      expect(result.current.fullQuestion?.description).toBe('Find two numbers that add up to target');
    });

    it('sets selectedQuestion immediately before async load', async () => {
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => { resolvePromise = resolve; });
      mockGetQuestion.mockReturnValue(promise);

      const { result } = renderHook(() => useQuestion());

      act(() => {
        result.current.selectQuestion(sampleQuestions[0]);
      });

      expect(result.current.selectedQuestion?.id).toBe('1');
      expect(result.current.isLoadingQuestion).toBe(true);

      await act(async () => {
        resolvePromise!(sampleFullQuestion);
      });

      expect(result.current.isLoadingQuestion).toBe(false);
    });

    it('sets error on failure', async () => {
      mockGetQuestion.mockRejectedValue(new Error('Question not found'));

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.selectQuestion(sampleQuestions[0]);
      });

      expect(result.current.error).toBe('Question not found');
      expect(result.current.selectedQuestion).toBeTruthy();
      expect(result.current.fullQuestion).toBeNull();
    });
  });

  describe('filters', () => {
    it('filters by difficulty', async () => {
      mockGetQuestions.mockResolvedValue(sampleQuestions);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      act(() => {
        result.current.setFilters({ difficulty: 'easy' });
      });

      expect(result.current.questions).toHaveLength(1);
      expect(result.current.questions[0].id).toBe('1');
      expect(result.current.allQuestions).toHaveLength(3);
    });

    it('filters by category', async () => {
      mockGetQuestions.mockResolvedValue(sampleQuestions);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      act(() => {
        result.current.setFilters({ category: 'linked-list' });
      });

      expect(result.current.questions).toHaveLength(1);
      expect(result.current.questions[0].title).toBe('Add Two Numbers');
    });

    it('combines multiple filters', async () => {
      mockGetQuestions.mockResolvedValue(sampleQuestions);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      act(() => {
        result.current.setFilters({ difficulty: 'hard', category: 'arrays' });
      });

      expect(result.current.questions).toHaveLength(1);
      expect(result.current.questions[0].title).toBe('Median of Two Sorted Arrays');
    });

    it('returns all questions when filters are empty', async () => {
      mockGetQuestions.mockResolvedValue(sampleQuestions);

      const { result } = renderHook(() => useQuestion());

      await act(async () => {
        await result.current.loadQuestions();
      });

      expect(result.current.questions).toHaveLength(3);
    });
  });

  describe('clearError', () => {
    it('clears error state', () => {
      const { result } = renderHook(() => useQuestion());
      act(() => { result.current.clearError(); });
      expect(result.current.error).toBeNull();
    });
  });
});
