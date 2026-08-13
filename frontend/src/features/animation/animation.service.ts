import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { AnimationScript, Question } from "@/types";

export interface AnimateQuestionInput {
  id?: string;
  title?: string;
  description?: string;
  category?: string;
  difficulty?: string;
  examples?: unknown[];
  test_cases?: unknown[];
  constraints?: string[];
  starter?: unknown;
}

export interface GenerateAnimationRequest {
  problem: string;
  code: string;
  language: string;
  difficulty?: string;
  lessonContext?: string;
  initialCode?: string;
  question?: AnimateQuestionInput;
}

function toQuestionInput(question: Question): AnimateQuestionInput {
  return {
    id: question.id,
    title: question.title,
    description: question.description,
    category: question.category,
    difficulty: question.difficulty,
    examples: question.examples,
    test_cases: question.test_cases,
    starter: question.starter,
  };
}

export class AnimationService {
  constructor(private http: HttpClient) {}

  async generateAnimation(
    request: GenerateAnimationRequest,
  ): Promise<AnimationScript> {
    const data = await this.http.post<{ animation: AnimationScript }>(
      "/api/coach/animate",
      {
        problem: request.problem,
        code: request.code,
        language: request.language.toLowerCase(),
        difficulty: request.difficulty ?? "medium",
        lesson_context: request.lessonContext,
        initial_code: request.initialCode,
        question: request.question ?? null,
      },
    );
    return data.animation;
  }
}

export function buildAnimateQuestion(
  question?: Question | null,
): AnimateQuestionInput | undefined {
  return question ? toQuestionInput(question) : undefined;
}

export const animationService = new AnimationService(new FetchClient());
