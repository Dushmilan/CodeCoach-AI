export interface TestCase {
  input: any[];
  expected: any;
  functionName: string;
  pythonFunctionName: string;
  javaFunctionName: string;
  inPlace?: boolean;
}

export interface Example {
  input: string;
  output: string;
}

export interface Question {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  description: string;
  starter: {
    python: string;
    javascript: string;
    java: string;
  };
  testCases: TestCase[];
  examples: Example[];
  hints: string[];
  solution: string;
  timeComplexity: string;
  spaceComplexity: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  apiKey?: string;
  preferences?: {
    theme: 'light' | 'dark';
    language: 'python' | 'javascript' | 'java';
    fontSize: number;
  };
}

export interface CodeCoachState {
  currentQuestion: Question | null;
  code: string;
  language: 'python' | 'javascript' | 'java';
  output: string;
  testResults: TestResult[];
  isLoading: boolean;
  error: string | null;
  user: User | null;
  apiKey: string | null;
}

export interface TestResult {
  testCase: TestCase;
  actualOutput: any;
  passed: boolean;
  executionResult: ExecutionResult;
  errorMessage?: string;
}

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  runtime: number;
  memory: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface HintRequest {
  questionId: string;
  code: string;
  language: string;
  previousHints?: string[];
}

export interface ReviewRequest {
  questionId: string;
  code: string;
  language: string;
  testResults?: TestResult[];
}

export interface ChatRequest {
  questionId: string;
  message: string;
  code?: string;
  language: string;
  conversationHistory?: ChatMessage[];
}

export interface ExecuteRequest {
  code: string;
  language: 'python' | 'javascript' | 'java';
  stdin?: string;
  args?: string[];
}

export interface TestRequest {
  code: string;
  language: 'python' | 'javascript' | 'java';
  testCases: TestCase[];
  functionName?: string;
  setupCode?: string;
}