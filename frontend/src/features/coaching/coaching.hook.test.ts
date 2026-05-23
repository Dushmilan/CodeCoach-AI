import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCoaching } from './coaching.hook';

const mockGetCoachResponse = vi.fn();

vi.mock('./coaching.service', () => ({
  coachingService: {
    getCoachResponse: (...args: unknown[]) => mockGetCoachResponse(...args),
  },
}));

beforeEach(() => {
  mockGetCoachResponse.mockReset();
});

describe('useCoaching', () => {
  describe('initial state', () => {
    it('starts with empty messages', () => {
      const { result } = renderHook(() => useCoaching());
      expect(result.current.messages).toEqual([]);
    });

    it('starts not typing', () => {
      const { result } = renderHook(() => useCoaching());
      expect(result.current.isTyping).toBe(false);
    });

    it('starts with no error', () => {
      const { result } = renderHook(() => useCoaching());
      expect(result.current.error).toBeNull();
    });
  });

  describe('clearMessages', () => {
    it('clears all messages', () => {
      const { result } = renderHook(() => useCoaching());
      act(() => { result.current.clearMessages(); });
      expect(result.current.messages).toEqual([]);
    });
  });

  describe('clearError', () => {
    it('clears error state', () => {
      const { result } = renderHook(() => useCoaching());
      act(() => { result.current.clearError(); });
      expect(result.current.error).toBeNull();
    });
  });

  describe('sendMessage', () => {
    const defaultArgs = {
      message: 'Help me',
      mode: 'hint' as const,
      problem: 'Two Sum',
      code: 'def two_sum(): pass',
      language: 'python',
    };

    it('adds user message and sets isTyping', async () => {
      mockGetCoachResponse.mockResolvedValue({
        response: 'Try a hash map',
        structured: null,
      });

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('Help me');
      expect(result.current.messages[1].role).toBe('assistant');
      expect(result.current.messages[1].content).toBe('Try a hash map');
      expect(result.current.isTyping).toBe(false);
    });

    it('sets isTyping true during request and false after', async () => {
      let resolvePromise: (value: unknown) => void;
      const promise = new Promise((resolve) => { resolvePromise = resolve; });
      mockGetCoachResponse.mockReturnValue(promise);

      const { result } = renderHook(() => useCoaching());

      act(() => {
        result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.isTyping).toBe(true);

      await act(async () => {
        resolvePromise!({ response: 'OK', structured: null });
      });

      expect(result.current.isTyping).toBe(false);
    });

    it('includes structured response data', async () => {
      const structured = {
        summary: 'Great work',
        hints: ['Try approach X'],
        code_review: null,
        complexity_analysis: null,
        suggestions: [],
        edge_cases: [],
        explanation: null,
        debug_help: null,
      };

      mockGetCoachResponse.mockResolvedValue({
        response: 'Here is help',
        structured,
      });

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.messages[1].structured).toEqual(structured);
    });

    it('handles empty message by using mode name', async () => {
      mockGetCoachResponse.mockResolvedValue({
        response: 'OK',
        structured: null,
      });

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          '',
          'review',
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.messages[0].content).toBe('review requested');
    });

    it('sets error state on failure', async () => {
      mockGetCoachResponse.mockRejectedValue(new Error('API error'));

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.error).toBe('API error');
    });

    it('adds fallback assistant message on error', async () => {
      mockGetCoachResponse.mockRejectedValue(new Error('Timeout'));

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[1].content).toBe('Sorry, I encountered an error. Please try again.');
    });

    it('handles non-Error rejection with generic message', async () => {
      mockGetCoachResponse.mockRejectedValue('string error');

      const { result } = renderHook(() => useCoaching());

      await act(async () => {
        await result.current.sendMessage(
          defaultArgs.message,
          defaultArgs.mode,
          defaultArgs.problem,
          defaultArgs.code,
          defaultArgs.language,
        );
      });

      expect(result.current.error).toBe('Failed to get coaching response');
    });
  });
});
