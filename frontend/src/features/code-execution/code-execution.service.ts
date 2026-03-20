import { CodeExecutionResult, TestCase, ValidationResponse } from './code-execution.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class CodeExecutionService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async runCode(
    language: string,
    code: string,
    version?: string
  ): Promise<CodeExecutionResult> {
    const response = await fetch(`${this.baseUrl}/api/run/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language, code, version }),
    });

    if (!response.ok) {
      throw new Error('Failed to run code');
    }

    const result = await response.json();
    console.log('Code execution result:', result);
    return result;
  }

  async validateCode(
    language: string,
    code: string,
    testCases: TestCase[]
  ): Promise<ValidationResponse> {
    const response = await fetch(`${this.baseUrl}/api/validate/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        language,
        code,
        test_cases: testCases,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to validate code');
    }

    return response.json();
  }
}

export const codeExecutionService = new CodeExecutionService();
