import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { StructuredCoachingResponse } from "@/types";
import {
  DebriefReport,
  DebriefExchangeInput,
} from "@/features/debrief/debrief.types";

export interface CoachingRequest {
  problem: string;
  code: string;
  message: string;
  mode: string;
  language: string;
  difficulty?: string;
  lesson_context?: string;
  chat_history?: { role: string; content: string }[];
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
    const data = await this.http.post<{
      response: string;
      structured: StructuredCoachingResponse | null;
    }>("/api/coach/", body);

    return {
      response: data.response,
      structured: data.structured || null,
    };
  }

  async getDebriefReport(
    problem: string,
    language: string,
    code: string,
    exchanges: DebriefExchangeInput[],
  ): Promise<DebriefReport> {
    const body = {
      problem,
      code,
      language: language.toLowerCase(),
      exchanges,
    };
    const data = await this.http.post<DebriefReport>("/api/coach/debrief-report", body);
    const rawExchanges = (data.exchanges as unknown as Array<
      DebriefReport["exchanges"][number] & {
        stronger_answer_should_include?: string[];
      }
    >) || [];
    return {
      summary: data.summary || "",
      takeaway: data.takeaway || "",
      exchanges: rawExchanges.map((ex) => ({
        question: ex.question || "",
        answer: ex.answer || "",
        strengths: ex.strengths || [],
        improvements: ex.improvements || [],
        strongerAnswer:
          ex.strongerAnswer || ex.stronger_answer_should_include || [],
      })),
    };
  }
}

export const coachingService = new CoachingService(new FetchClient());
