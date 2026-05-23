"use client";

import { useCallback } from 'react';
import { Question, Language } from '@/types';
import { useCodeExecution } from '@/features/code-execution/code-execution.hook';
import { useLocalStorage } from '@/hooks';

interface UseCodeRunnerOptions {
  fullQuestion: Question | null;
  language: Language;
  currentCode: string;
}

interface UseCodeRunnerReturn {
  userProgress: Record<string, 'attempted' | 'solved'>;
  setUserProgress: (
    updater: (prev: Record<string, 'attempted' | 'solved'>) => Record<string, 'attempted' | 'solved'>
  ) => void;
  handleRunCode: () => Promise<void>;
  handleSubmitCode: () => Promise<void>;
  isRunning: boolean;
  output: string;
  executionError: string | null;
  clearOutput: () => void;
  clearExecutionError: () => void;
}

export function useCodeRunner({
  fullQuestion,
  language,
  currentCode,
}: UseCodeRunnerOptions): UseCodeRunnerReturn {
  const {
    isRunning,
    output,
    error: executionError,
    validateCode,
    submitCode,
    runLocalJavaScript,
    clearOutput,
    clearError: clearExecutionError,
  } = useCodeExecution();

  const [userProgress, setUserProgress] = useLocalStorage<Record<string, 'attempted' | 'solved'>>(
    'user_progress',
    {}
  );

  const handleRunCode = useCallback(async () => {
    if (!fullQuestion) return;

    if (language === 'javascript') {
      try {
        await runLocalJavaScript(currentCode, fullQuestion);
      } catch (err) {
        console.error('JavaScript execution error:', err);
      }
      return;
    }

    try {
      const visibleTestCases = fullQuestion.test_cases.filter((tc) => !tc.hidden).slice(0, 3);
      await validateCode(language, currentCode, visibleTestCases);
      setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: 'attempted' }));
    } catch (err) {
      console.error('Code execution error:', err);
    }
  }, [fullQuestion, language, currentCode, validateCode, runLocalJavaScript, setUserProgress]);

  const handleSubmitCode = useCallback(async () => {
    if (!fullQuestion) return;

    try {
      const result = await submitCode(fullQuestion.id, language, currentCode);

      if (result.passed_count === result.total) {
        setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: 'solved' }));
      } else {
        setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: 'attempted' }));
      }
    } catch (err) {
      console.error('Submit error:', err);
    }
  }, [fullQuestion, language, currentCode, submitCode, setUserProgress]);

  return {
    userProgress,
    setUserProgress,
    handleRunCode,
    handleSubmitCode,
    isRunning,
    output,
    executionError,
    clearOutput,
    clearExecutionError,
  };
}
