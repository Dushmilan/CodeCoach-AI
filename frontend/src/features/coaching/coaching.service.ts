import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { StructuredCoachingResponse } from "@/types";

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
  question_id?: string;
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
    questionId?: string,
  ): Promise<CoachingResponse> {
    const body: CoachingRequest = {
      problem,
      code,
      message,
      mode: mode.toLowerCase(),
      language: language.toLowerCase(),
      difficulty,
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
}

export const coachingService = new CoachingService(new FetchClient());
