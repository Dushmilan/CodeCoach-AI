import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCodeRunner } from './use-code-runner.hook';
import { Question } from '@/types';

const mockValidateCode = vi.fn();
const mockSubmitCode = vi.fn();
const mockRunLocalJavaScript = vi.fn();
const mockClearOutput = vi.fn();
const mockClearExecutionError = vi.fn();

vi.mock('@/features/code-execution/code-execution.hook', () => ({
  useCodeExecution: vi.fn(() => ({
    isRunning: false,
    output: '',
    error: null,
    validateCode: mockValidateCode,
    submitCode: mockSubmitCode,
    runLocalJavaScript: mockRunLocalJavaScript,
    clearOutput: mockClearOutput,
    clearError: mockClearExecutionError,
  })),
}));

const mockLocalStorage = vi.fn(() => ({}));
let mockLocalStorageSetter = vi.fn();

vi.mock('@/hooks', () => ({
  useLocalStorage: vi.fn((key: string, initial: Record<string, 'attempted' | 'solved'>) => {
    const val = mockLocalStorage();
    mockLocalStorageSetter = vi.fn((updater) => {
      const next = updater(val);
      Object.assign(val, next);
    });
    return [val, mockLocalStorageSetter];
  }),
}));

const question: Question = {
  id: 'q1',
  title: 'Test',
  difficulty: 'easy',
  category: 'arrays',
  company_tags: [],
  description: 'Test question.',
  starter: { python: 'def f(): pass', javascript: 'function f() {}', java: '' },
  examples: [],
  test_cases: [
    { input: '1', expected_output: '2', hidden: false },
    { input: '3', expected_output: '4', hidden: true },
    { input: '5', expected_output: '6', hidden: false },
  ],
  hints: [],
  solution: '',
  time_complexity: '',
  space_complexity: '',
};

const noTestCasesQuestion: Question = {
  ...question,
  test_cases: [
    { input: '1', expected_output: '2', hidden: false },
    { input: '3', expected_output: '4', hidden: false },
    { input: '5', expected_output: '6', hidden: false },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useCodeRunner', () => {
  describe('handleRunCode', () => {
    it('calls runLocalJavaScript when language is javascript', async () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'javascript', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockRunLocalJavaScript).toHaveBeenCalledWith('code', question);
      expect(mockValidateCode).not.toHaveBeenCalled();
    });

    it('calls validateCode with non-hidden test cases for non-js languages', async () => {
      mockSubmitCode.mockResolvedValue({ passed_count: 2, total: 3, results: [] });

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockValidateCode).toHaveBeenCalledWith('python', 'code', [
        { input: '1', expected_output: '2', hidden: false },
        { input: '5', expected_output: '6', hidden: false },
      ]);
    });

    it('does nothing when fullQuestion is null', async () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: null, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockRunLocalJavaScript).not.toHaveBeenCalled();
      expect(mockValidateCode).not.toHaveBeenCalled();
    });

    it('updates user progress to attempted after non-JS run', async () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockLocalStorageSetter).toHaveBeenCalled();
    });

    it('handles errors in JS execution gracefully', async () => {
      mockRunLocalJavaScript.mockRejectedValue(new Error('JS error'));

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'javascript', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockRunLocalJavaScript).toHaveBeenCalled();
    });

    it('handles errors in non-JS execution gracefully', async () => {
      mockValidateCode.mockRejectedValue(new Error('Execution error'));

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleRunCode();
      });

      expect(mockValidateCode).toHaveBeenCalled();
    });
  });

  describe('handleSubmitCode', () => {
    it('calls submitCode with correct params', async () => {
      mockSubmitCode.mockResolvedValue({ passed_count: 3, total: 3, results: [] });

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleSubmitCode();
      });

      expect(mockSubmitCode).toHaveBeenCalledWith('q1', 'python', 'code');
    });

    it('sets progress to solved when all tests pass', async () => {
      mockSubmitCode.mockResolvedValue({ passed_count: 3, total: 3, results: [] });

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleSubmitCode();
      });

      expect(mockLocalStorageSetter).toHaveBeenCalled();
    });

    it('sets progress to attempted when some tests fail', async () => {
      mockSubmitCode.mockResolvedValue({ passed_count: 1, total: 3, results: [] });

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleSubmitCode();
      });

      expect(mockLocalStorageSetter).toHaveBeenCalled();
    });

    it('does nothing when fullQuestion is null', async () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: null, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleSubmitCode();
      });

      expect(mockSubmitCode).not.toHaveBeenCalled();
    });

    it('handles submit errors gracefully', async () => {
      mockSubmitCode.mockRejectedValue(new Error('Submit error'));

      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: 'code' })
      );

      await act(async () => {
        await result.current.handleSubmitCode();
      });

      expect(mockSubmitCode).toHaveBeenCalled();
    });
  });

  describe('state', () => {
    it('starts with empty userProgress', () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: '' })
      );

      expect(result.current.userProgress).toEqual({});
    });

    it('exposes isRunning, output, executionError from useCodeExecution', () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: '' })
      );

      expect(result.current.isRunning).toBe(false);
      expect(result.current.output).toBe('');
      expect(result.current.executionError).toBeNull();
    });

    it('exposes clearOutput and clearExecutionError', () => {
      const { result } = renderHook(() =>
        useCodeRunner({ fullQuestion: question, language: 'python', currentCode: '' })
      );

      act(() => result.current.clearOutput());
      expect(mockClearOutput).toHaveBeenCalled();

      act(() => result.current.clearExecutionError());
      expect(mockClearExecutionError).toHaveBeenCalled();
    });
  });
});
