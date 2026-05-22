"use client";

import { useState, useCallback } from 'react';
import { Question } from '@/types';
import { codeExecutionService } from './code-execution.service';
import { CodeExecutionFeature, SubmitResponse, TestCase, ValidationResponse } from './code-execution.types';

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
      try {
        const result = await codeExecutionService.validateCode(language, code, testCases);
        setLastResult(result);
        return result;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to validate code';
        setError(errorMessage);
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
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const runLocalJavaScript = useCallback(
    async (code: string, question: Question, fnName?: string): Promise<string> => {
      setIsRunning(true);
      setError(null);
      const logs: string[] = [];

      const originalConsoleLog = console.log;
      const originalConsoleError = console.error;
      const originalConsoleWarn = console.warn;

      const captureLog = (...args: any[]) => {
        const formattedArgs = args.map((arg) =>
          typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        ).join(' ');
        logs.push(formattedArgs);
        originalConsoleLog(...args);
      };

      console.log = captureLog;
      console.error = captureLog;
      console.warn = captureLog;

      try {
        const jsStarter = question.starter.javascript;
        const functionName =
          fnName ||
          jsStarter.match(/function\s+(\w+)\s*\(/)?.[1] ||
          jsStarter.match(/var\s+(\w+)\s*=\s*function/)?.[1] ||
          jsStarter.match(/const\s+(\w+)\s*=/)?.[1];

        if (!functionName) {
          throw new Error('Could not identify the target function name for testing.');
        }

        const testRunner = new Function(
          'testCases',
          `
          ${code}

          if (typeof ${functionName} !== 'function') {
            throw new Error('Function "${functionName}" is not defined or is not a function.');
          }

          return testCases.map((tc, index) => {
            try {
              const inputLines = tc.input.split('\\n');
              const parsedArgs = inputLines.map(line => JSON.parse(line));
              const result = ${functionName}(...parsedArgs);
              const expectedOutput = JSON.parse(tc.expected_output);
              const passed = JSON.stringify(result) === JSON.stringify(expectedOutput);
              return { index: index + 1, passed, input: tc.input, expected: tc.expected_output, actual: result };
            } catch (e) {
              return { index: index + 1, passed: false, error: e.message, input: tc.input };
            }
          });
        `
        );

        const results = testRunner(question.test_cases);

        let outputText = logs.length > 0 ? `Console Output:\n${logs.join('\n')}\n\n` : '';
        outputText += 'Test Results:\n\n';

        let allPassed = true;
        results.forEach((r: any) => {
          const testCase = question.test_cases[r.index - 1];
          const status = r.passed ? 'Pass' : 'Fail';
          outputText += `${r.passed ? '✅' : '❌'} Test Case ${r.index}:\n`;
          outputText += `   Status: ${status}\n`;
          outputText += `   Input: ${r.input}\n`;
          outputText += `   Expected Output: ${r.expected}\n`;
          if (r.error) {
            outputText += `   Actual Output: (Error) ${r.error}\n`;
          } else {
            outputText += `   Actual Output: ${JSON.stringify(r.actual)}\n`;
          }
          outputText += '\n';
          if (!r.passed) allPassed = false;
        });

        setOutput(outputText);
        return outputText;
      } catch (err: any) {
        const errorMessage = err.message || 'An error occurred during execution';
        setError(errorMessage);
        throw err;
      } finally {
        console.log = originalConsoleLog;
        console.error = originalConsoleError;
        console.warn = originalConsoleWarn;
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
