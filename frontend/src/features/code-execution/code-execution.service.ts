import { HttpClient } from '@/lib/http-client';
import { FetchClient } from '@/lib/fetch-client';
import { CodeExecutionResult, SubmitResponse, TestCase, TestResult, ValidationResponse } from './code-execution.types';

export class CodeExecutionService {
  constructor(private http: HttpClient) {}

  async runCode(
    language: string,
    code: string,
    stdin?: string,
    version?: string
  ): Promise<CodeExecutionResult> {
    return this.http.post<CodeExecutionResult>('/api/run/', {
      language,
      code,
      stdin: stdin || '',
      version,
    });
  }

  async validateCode(
    language: string,
    code: string,
    testCases: TestCase[],
    questionId?: string
  ): Promise<ValidationResponse> {
    const results: TestResult[] = [];
    let passedCount = 0;

    for (const tc of testCases) {
      try {
        const execResult = await this.runCode(language, code, tc.input);
        const actual = (execResult.stdout || '').trim();
        const expected = tc.expected_output.trim();
        const isPassed = actual === expected;
        if (isPassed) passedCount++;
        results.push({
          test_name: tc.description || `Test ${results.length + 1}`,
          passed: isPassed,
          stdout: execResult.stdout || '',
          stderr: execResult.stderr || '',
        });
      } catch (err) {
        results.push({
          test_name: tc.description || `Test ${results.length + 1}`,
          passed: false,
          stdout: '',
          stderr: err instanceof Error ? err.message : 'Execution failed',
        });
      }
    }

    return {
      total_tests: testCases.length,
      passed_tests: passedCount,
      success_rate: testCases.length > 0 ? passedCount / testCases.length : 0,
      results,
      formatted_output: '',
    };
  }

  async submitCode(
    questionId: string,
    language: string,
    code: string,
  ): Promise<SubmitResponse> {
    return this.http.post<SubmitResponse>('/api/submit/', {
      question_id: questionId,
      language,
      code,
    });
  }
}

export const codeExecutionService = new CodeExecutionService(new FetchClient());
