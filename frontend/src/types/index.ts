export interface Question {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  company_tags: string[];
  description: string;
  starter: {
    python: string;
    javascript: string;
    java: string;
  };
  examples: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
  test_cases: Array<{
    input: any[];
    expected: any;
  }>;
  hints: string[];
  solution: string;
  time_complexity: string;
  space_complexity: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface CodeExecutionResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  runtime?: number;
}

export interface UserProgress {
  question_id: string;
  status: 'attempted' | 'solved';
  language: string;
  code: string;
  solved_at?: Date;
  attempts: number;
}

export type Language = 'python' | 'javascript' | 'java';