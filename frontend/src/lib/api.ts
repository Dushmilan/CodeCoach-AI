import { Question, QuestionSummary, CodeExecutionResult } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getQuestions(): Promise<QuestionSummary[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    try {
      const response = await fetch(`${this.baseUrl}/api/questions`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch questions: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      return data.questions || [];
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      throw error;
    }
  }

  async getQuestion(id: string): Promise<Question> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    try {
      const response = await fetch(`${this.baseUrl}/api/questions/${id}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch question: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }
      throw error;
    }
  }

  async runCode(language: string, code: string, version?: string): Promise<CodeExecutionResult> {
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
    testCases: Array<{ input: string; expected_output: string; description?: string }>
  ): Promise<{
    total_tests: number;
    passed_tests: number;
    success_rate: number;
    results: Array<{
      test_name: string;
      passed: boolean;
      stdout: string;
      stderr: string;
      error?: string;
    }>;
    formatted_output: string;
  }> {
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

  async getCoachResponse(
    problem: string,
    language: string,
    code: string,
    message: string,
    mode: string
  ): Promise<ReadableStream<Uint8Array>> {
    const response = await fetch(`${this.baseUrl}/api/coach/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        problem,
        code,
        message,
        mode: mode.toLowerCase(),
        language: language.toLowerCase(),
        difficulty: 'medium'
      }),
    });
    if (!response.ok) {
      throw new Error('Failed to get coaching response');
    }
    if (!response.body) {
      throw new Error('Response body is null');
    }
    return response.body;
  }
}

export const api = new ApiClient(API_BASE_URL);
