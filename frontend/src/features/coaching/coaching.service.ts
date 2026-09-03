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
}

export interface CoachingResponse {
  response: string;
  structured: StructuredCoachingResponse | null;
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
    const data = await this.http.post<{
      response: string;
      structured: StructuredCoachingResponse | null;
    }>("/api/coach/", body);

    return {
      response: data.response,
      structured: data.structured || null,
    };
  }
}

export const coachingService = new CoachingService(new FetchClient());
