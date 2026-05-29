"use client";

import { useState, useCallback } from 'react';
import { Question } from '@/types';
import { codeExecutionService } from './code-execution.service';
import { CodeExecutionFeature, SubmitResponse, TestCase, ValidationResponse } from './code-execution.types';
import { executeClientJS, formatClientJsOutput } from '@/lib/client-js-executor';
import { showToast } from '@/components/ui/Toast';

export function useCodeExecution(): CodeExecutionFeature {
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<ValidationResponse | null>(null);
  const [lastSubmitResult, setLastSubmitResult] = useState<SubmitResponse | null>(null);

  const runCode = useCallback(
    async (language: string, code: string, version?: string) => {
      setIsRunning(true);
      setError(null);
      try {
        const result = await codeExecutionService.runCode(language, code, version);
        setOutput(result.stdout || '');
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to run code';
        setError(errorMessage);
        showToast(errorMessage, 'error');
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const validateCode = useCallback(
    async (language: string, code: string, testCases: TestCase[]) => {
      setIsRunning(true);
      setError(null);
      setOutput('');
      try {
        const result = await codeExecutionService.validateCode(language, code, testCases);
        setLastResult(result);

        const lines: string[] = [];
        lines.push(`Run Results: ${result.passed_tests}/${result.total_tests} passed\n`);
        result.results.forEach((r, index) => {
          const tc = testCases[index];
          lines.push(`${r.passed ? '✅' : '❌'} ${r.test_name || `Test ${index + 1}`}:`);
          lines.push(`   Status: ${r.passed ? 'Pass' : 'Fail'}`);
          lines.push(`   Input: ${tc.input}`);
          lines.push(`   Expected Output: ${tc.expected_output}`);
          lines.push(`   Actual Output: ${normalizeDisplayJson(r.stdout) || '(empty)'}`);
          if (r.error) lines.push(`   Error: ${r.error}`);
          if (r.stderr) lines.push(`   Stderr: ${r.stderr}`);
        });
        setOutput(lines.join('\n'));

        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to validate code';
        setError(errorMessage);
        showToast(errorMessage, 'error');
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const submitCode = useCallback(
    async (questionId: string, language: string, code: string): Promise<SubmitResponse> => {
      setIsRunning(true);
      setError(null);
      try {
        const result = await codeExecutionService.submitCode(questionId, language, code);
        setLastSubmitResult(result);
        const outputLines = result.results.map((r) => {
          const status = r.passed ? 'Pass' : 'Fail';
          let line = `${r.passed ? '✅' : '❌'} Test ${r.index}: ${status}`;
          if (!r.hidden) {
            line += ` | Input: ${r.input} | Expected: ${r.expected} | Actual: ${r.actual}`;
          }
          return line;
        });
        setOutput(`Submit Results: ${result.passed_count}/${result.total} passed\n\n${outputLines.join('\n')}`);
        setLastResult({
          total_tests: result.total,
          passed_tests: result.passed_count,
          success_rate: result.total > 0 ? result.passed_count / result.total : 0,
          results: result.results.map((r) => ({
            test_name: `Test ${r.index}`,
            passed: r.passed,
            stdout: r.actual,
            stderr: '',
          })),
          formatted_output: '',
        });
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to submit code';
        setError(errorMessage);
        showToast(errorMessage, 'error');
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const runLocalJavaScript = useCallback(
    async (code: string, question: Question): Promise<string> => {
      setIsRunning(true);
      setError(null);

      try {
        const result = executeClientJS(code, question);
        const outputText = formatClientJsOutput(result, question);
        setOutput(outputText);
        return outputText;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred during execution';
        setError(errorMessage);
        showToast(errorMessage, 'error');
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const clearOutput = useCallback(() => {
    setOutput('');
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isRunning,
    output,
    error,
    lastResult,
    lastSubmitResult,
    runCode,
    validateCode,
    submitCode,
    runLocalJavaScript,
    clearOutput,
    clearError,
  };
}

function normalizeDisplayJson(s: string): string {
  try {
    return JSON.stringify(JSON.parse(s));
  } catch {
    return s;
  }
}
