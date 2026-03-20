import { Question, QuestionSummary, CodeExecutionResult } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async getQuestions(): Promise<QuestionSummary[]> {
    const response = await fetch(`${this.baseUrl}/api/questions`);
    if (!response.ok) {
      throw new Error('Failed to fetch questions');
    }
    const data = await response.json();
    return data.questions || [];
  }

  async getQuestion(id: string): Promise<Question> {
    const response = await fetch(`${this.baseUrl}/api/questions/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch question');
    }
    return response.json();
  }

  async runCode(language: string, code: string, version?: string): Promise<CodeExecutionResult> {
    const response = await fetch(`${this.baseUrl}/api/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language, code, version }),
    });
    if (!response.ok) {
      throw new Error('Failed to run code');
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
