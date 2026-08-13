import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { RecommendedQuestion } from "@/types";

export class SkillGraphService {
  constructor(private http: HttpClient) {}

  async getRecommendedQuestions(limit: number = 5): Promise<RecommendedQuestion[]> {
    return this.http.get<RecommendedQuestion[]>(
      `/api/skills/me/recommended-questions?limit=${limit}`,
      {
        cache: "no-store",
      },
    );
  }
}

export const skillGraphService = new SkillGraphService(new FetchClient());
