import { Language, Question } from '@/types';

export interface TestCase {
  input: string;
  expected_output: string;
  description?: string;
}

export interface CodeExecutionResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  runtime?: number;
}

export interface TestResult {
  test_name: string;
  passed: boolean;
  stdout: string;
  stderr: string;
  error?: string;
}

export interface ValidationResponse {
  total_tests: number;
  passed_tests: number;
  success_rate: number;
  results: TestResult[];
  formatted_output: string;
}

export interface CodeExecutionState {
  isRunning: boolean;
  output: string;
  error: string | null;
  lastResult: ValidationResponse | null;
}

export interface CodeExecutionActions {
  runCode: (language: string, code: string, version?: string) => Promise<CodeExecutionResult>;
  validateCode: (
    language: string,
    code: string,
    testCases: TestCase[]
  ) => Promise<ValidationResponse>;
  runLocalJavaScript: (code: string, question: Question, fnName?: string) => Promise<string>;
  clearOutput: () => void;
  clearError: () => void;
}

export type CodeExecutionFeature = CodeExecutionState & CodeExecutionActions;
