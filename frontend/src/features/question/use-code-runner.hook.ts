"use client";

import { useCallback } from "react";
import { Question, Language } from "@/types";
import { useCodeExecution } from "@/features/code-execution/code-execution.hook";
import {
  SubmitResponse,
  TestCaseResultView,
} from "@/features/code-execution/code-execution.types";
import { useLocalStorage } from "@/hooks";
import { showToast } from "@/components/ui/Toast";
import { useAuth } from "@/providers";

interface UseCodeRunnerOptions {
  fullQuestion: Question | null;
  language: Language;
  currentCode: string;
}

interface UseCodeRunnerReturn {
  userProgress: Record<string, "attempted" | "solved">;
  setUserProgress: (
    updater: (
      prev: Record<string, "attempted" | "solved">,
    ) => Record<string, "attempted" | "solved">,
  ) => void;
  handleRunCode: (stdin?: string) => Promise<void>;
  handleSubmitCode: () => Promise<void>;
  isRunning: boolean;
  output: string;
  testResults: TestCaseResultView[] | null;
  lastSubmitResult: SubmitResponse | null;
  executionError: string | null;
  clearOutput: () => void;
  clearExecutionError: () => void;
  isAuthenticated: boolean;
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
    testResults,
    lastSubmitResult,
    validateCode,
    submitCode,
    runLocalJavaScript,
    clearOutput,
    clearError: clearExecutionError,
  } = useCodeExecution();

  const { isAuthenticated } = useAuth();

  const [userProgress, setUserProgress] = useLocalStorage<
    Record<string, "attempted" | "solved">
  >("user_progress", {});

  const handleRunCode = useCallback(
    async (stdin?: string) => {
      if (!fullQuestion) return;
      if (!isAuthenticated) {
        showToast("Please sign in to run code", "error");
        return;
      }

      if (language === "javascript") {
        try {
          await runLocalJavaScript(currentCode, fullQuestion);
        } catch (err) {
          console.error("JavaScript execution error:", err);
        }
        return;
      }

      try {
        if (fullQuestion.is_interactive && stdin) {
          await validateCode(language, currentCode, [
            { input: stdin, expected_output: "..." },
          ], fullQuestion.id);
        } else {
          const visibleTestCases = fullQuestion.test_cases
            .filter((tc) => !tc.hidden)
            .slice(0, 3);
          await validateCode(language, currentCode, visibleTestCases);
        }
        setUserProgress((prev) => ({
          ...prev,
          [fullQuestion.id]: "attempted",
        }));
      } catch (err) {
        console.error("Code execution error:", err);
      }
    },
    [
      fullQuestion,
      language,
      currentCode,
      validateCode,
      runLocalJavaScript,
      setUserProgress,
      isAuthenticated,
    ],
  );

  const handleSubmitCode = useCallback(async () => {
    if (!fullQuestion) return;
    if (!isAuthenticated) {
      showToast("Please sign in to submit code", "error");
      return;
    }

    try {
      const result = await submitCode(fullQuestion.id, language, currentCode);

      if (result.passed_count === result.total) {
        setUserProgress((prev) => ({ ...prev, [fullQuestion.id]: "solved" }));
        showToast("All tests passed!", "success");
      } else {
        setUserProgress((prev) => ({
          ...prev,
          [fullQuestion.id]: "attempted",
        }));
        showToast(
          `${result.passed_count}/${result.total} tests passed`,
          "info",
        );
      }
    } catch (err) {
      console.error("Submit error:", err);
    }
  }, [
    fullQuestion,
    language,
    currentCode,
    submitCode,
    setUserProgress,
    isAuthenticated,
  ]);

  return {
    userProgress,
    setUserProgress,
    handleRunCode,
    handleSubmitCode,
    isRunning,
    output,
    testResults,
    lastSubmitResult,
    executionError,
    clearOutput,
    clearExecutionError,
    isAuthenticated,
  };
}
