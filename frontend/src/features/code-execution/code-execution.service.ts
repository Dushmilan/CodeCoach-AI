import { HttpClient } from '@/lib/http-client';
import { FetchClient } from '@/lib/fetch-client';
import { CodeExecutionResult, TestCase, ValidationResponse } from './code-execution.types';

export class CodeExecutionService {
  constructor(private http: HttpClient) {}

  async runCode(
    language: string,
    code: string,
    version?: string
  ): Promise<CodeExecutionResult> {
    const result = await this.http.post<CodeExecutionResult>('/api/run/', {
      language,
      code,
      version,
    });
    return result;
  }

  async validateCode(
    language: string,
    code: string,
    testCases: TestCase[]
  ): Promise<ValidationResponse> {
    return this.http.post<ValidationResponse>('/api/validate/validate', {
      language,
      code,
      test_cases: testCases,
    });
  }
}

export const codeExecutionService = new CodeExecutionService(new FetchClient());
