export interface QuestionSummary {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  category: string;
  company_tags: string[];
  solved?: boolean;
}

export type RecommendationReason =
  | "weak_skill"
  | "missing_prerequisite"
  | "due_for_review"
  | "new_skill"
  | "strengthen";

export interface RecommendedQuestion {
  skill_slug: string;
  skill_name: string;
  reason: RecommendationReason;
  reason_text: string;
  question: Question;
}

export interface Question extends QuestionSummary {
  description: string;
  starter: {
    python: string;
    javascript: string;
    java: string;
    cpp: string;
    c: string;
    go: string;
    rust: string;
    typescript: string;
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

export type AnimationOperation =
  | "compare"
  | "visit"
  | "swap"
  | "move"
  | "insert"
  | "remove"
  | "mark"
  | "output"
  | "compare_code";

export type AnimationResult =
  | "checking"
  | "match"
  | "mismatch"
  | "complete";

export type SceneShapeType = "rect" | "ellipse" | "line" | "polygon" | "text";

export interface SceneShape {
  id: string;
  type: SceneShapeType;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  radius?: number;
  points?: [number, number][];
  text?: string;
  fontSize?: number;
  fill?: string;
  stroke?: string;
  lineWidth?: number;
  opacity?: number;
}

export type MotionOpName =
  | "appear"
  | "disappear"
  | "move"
  | "fill"
  | "stroke"
  | "scale"
  | "rotate"
  | "label";

export interface MotionOp {
  target: string;
  op: MotionOpName;
  to?: unknown;
  duration: number;
}

export interface AnimationStep {
  // Generic scene fields (current contract)
  narration: string;
  shapes?: SceneShape[];
  motion?: MotionOp[];
  // Legacy typed-frame fields (kept optional for backward compatibility)
  operation?: AnimationOperation | null;
  index?: number | null;
  from_index?: number | null;
  to_index?: number | null;
  value?: unknown;
  line_number?: number | null;
  user_line?: string | null;
  solution_line?: string | null;
  result?: AnimationResult | null;
}

export interface AnimationScript {
  // `type` is legacy; the current contract is a generic declarative scene.
  type?: string;
  title?: string;
  data: Record<string, unknown>;
  steps: AnimationStep[];
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
  animation?: AnimationScript | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
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
  status: "attempted" | "solved";
  language: string;
  code: string;
  solved_at?: Date;
  attempts: number;
}

export type Language =
  "python" | "javascript" | "java" | "cpp" | "c" | "go" | "rust" | "typescript";

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
  type: "theory" | "exercise";
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
  role?: string;
  plan?: string;
}

export interface SkillSummary {
  skill_slug: string;
  name: string;
  mastery_score: number;
  confidence: number;
  status: "new" | "learning" | "developing" | "strong" | "needs_review";
  trend: "improving" | "declining" | "stable";
  evidence_count: number;
  recent_error_count: number;
  last_seen_at: string | null;
  last_reviewed_at: string | null;
}

export interface SkillGraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface SkillGraphResponse {
  skills: SkillSummary[];
  edges: SkillGraphEdge[];
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isHydrated: boolean;
}
