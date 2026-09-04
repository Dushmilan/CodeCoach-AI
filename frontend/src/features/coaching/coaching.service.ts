import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { StructuredCoachingResponse } from "@/types";
import { CoachingSurface } from "./coaching.types";

export interface CoachingRequest {
  problem: string;
  code: string;
  message: string;
  mode: string;
  language: string;
  difficulty?: string;
  lesson_context?: string;
  chat_history?: { role: string; content: string }[];
  initial_code?: string;
  surface: CoachingSurface;
  question_id?: string;
}

export interface CoachingResponse {
  response: string;
  structured: StructuredCoachingResponse | null;
}

export interface WarmResponse {
  status: string;
  warmed: boolean;
  ttl: number;
}

export class CoachingService {
  constructor(private http: HttpClient) {}

  async getCoachResponse(
    problem: string,
    language: string,
    code: string,
    message: string,
    mode: string,
    difficulty: string = "medium",
    lessonContext?: string,
    chatHistory?: { role: string; content: string }[],
    initialCode?: string,
    surface: CoachingSurface = "questions",
    questionId?: string,
  ): Promise<CoachingResponse> {
    const body: CoachingRequest = {
      problem,
      code,
      message,
      mode: mode.toLowerCase(),
      language: language.toLowerCase(),
      difficulty,
      surface,
    };
    if (lessonContext) {
      body.lesson_context = lessonContext;
    }
    if (chatHistory && chatHistory.length > 0) {
      body.chat_history = chatHistory;
    }
    if (initialCode !== undefined) {
      body.initial_code = initialCode;
    }
    if (questionId) {
      body.question_id = questionId;
    }
    const data = await this.http.post<{
      response: string;
      structured: StructuredCoachingResponse | null;
    }>("/api/coach/", body);

    return {
      response: data.response,
      structured: data.structured || null,
    };
  }

  async warmContext(
    questionId: string,
    signal?: AbortSignal,
  ): Promise<WarmResponse> {
    try {
      return await this.http.post<WarmResponse>(
        "/api/coach/warm",
        { question_id: questionId },
        signal ? { signal } : undefined,
      );
    } catch {
      return { status: "error", warmed: false, ttl: 0 };
    }
  }
}

export const coachingService = new CoachingService(new FetchClient());
