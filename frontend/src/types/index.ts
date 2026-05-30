export interface QuestionSummary {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  company_tags: string[];
  solved?: boolean;
}

export interface Question extends QuestionSummary {
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
    input: string;
    expected_output: string;
    description?: string;
    hidden?: boolean;
  }>;
  hints: string[];
  solution: string;
  time_complexity: string;
  space_complexity: string;
  is_interactive?: boolean;
}

export interface StructuredCoachingResponse {
  summary: string;
  hints: string[];
  code_review: string | null;
  complexity_analysis: string | null;
  suggestions: string[];
  edge_cases: string[];
  explanation: string | null;
  debug_help: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  structured?: StructuredCoachingResponse | null;
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

export interface CourseSummary {
  id: string;
  title: string;
  description: string;
  language: string;
  icon: string;
  order: number;
  progress: number;
}

export interface CourseDetail {
  id: string;
  title: string;
  description: string;
  language: string;
  icon: string;
  order: number;
  modules: ModuleDetail[];
}

export interface ModuleDetail {
  id: string;
  course_id: string;
  title: string;
  description: string;
  order: number;
  lessons: LessonSummary[];
}

export interface LessonSummary {
  id: string;
  course_id: string;
  module_id: string;
  title: string;
  type: 'theory' | 'exercise';
  content: string;
  order: number;
  starter_code: string | null;
  test_cases: Array<{
    input: string;
    expected_output: string;
    description: string;
  }> | null;
  question_id: string | null;
  language: string;
}

export interface CourseProgress {
  user_id: string;
  course_id: string;
  completed_lessons: string[];
  last_accessed_lesson_id: string | null;
  started_at: string;
  last_accessed_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  is_active: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isHydrated: boolean;
}
