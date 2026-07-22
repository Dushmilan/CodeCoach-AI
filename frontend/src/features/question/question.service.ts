import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { Question, QuestionSummary } from "@/types";

export class QuestionService {
  constructor(private http: HttpClient) {}

  async getQuestions(): Promise<QuestionSummary[]> {
    const data = await this.http.get<{ questions: QuestionSummary[] }>(
      "/api/questions",
      {
        cache: "no-store",
      },
    );
    return data.questions || [];
  }

  async getQuestion(id: string): Promise<Question> {
    return this.http.get<Question>(`/api/questions/${id}`, {
      cache: "no-store",
    });
  }
}

export const questionService = new QuestionService(new FetchClient());
