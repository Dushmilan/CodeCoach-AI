import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { Question, QuestionSummary } from "@/types";

export class QuestionService {
  constructor(private http: HttpClient) {}

  async getQuestions(): Promise<QuestionSummary[]> {
    // Fetch all questions paginated (per_page=100) — backend optimized for summary columns, single page ~1.4s
    // Total 107 needs 2 pages; loop until total collected. Keeps client-side filtering correct while enabling infinite scroll rendering.
    const perPage = 100;
    let page = 1;
    let all: QuestionSummary[] = [];
    let total: number | null = null;
    while (total === null || all.length < total) {
      const data = await this.http.get<{
        questions: QuestionSummary[];
        total: number;
        page: number;
        per_page: number;
      }>(`/api/questions?page=${page}&per_page=${perPage}`, {
        cache: "no-store",
      });
      const batch = data.questions || [];
      all = all.concat(batch);
      total = data.total ?? batch.length;
      if (batch.length < perPage) break;
      page += 1;
      // Safety: never loop more than 10 pages
      if (page > 10) break;
    }
    return all;
  }

  async getQuestion(id: string): Promise<Question> {
    return this.http.get<Question>(`/api/questions/${id}`, {
      cache: "no-store",
    });
  }
}

export const questionService = new QuestionService(new FetchClient());
