import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { RecommendedQuestion, SkillGraphResponse } from "@/types";

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

  async getGraph(includeBoilerplate = false): Promise<SkillGraphResponse> {
    const qs = includeBoilerplate ? "?include_boilerplate=true" : "";
    return this.http.get<SkillGraphResponse>(`/api/skills/me/skills${qs}`, {
      cache: "no-store",
    });
  }

  async syncFromSubmissions(): Promise<{ accepted: number; duplicate: number; invalid: number; skipped: number }> {
    return this.http.post<{ accepted: number; duplicate: number; invalid: number; skipped: number }>(
      `/api/skills/me/sync`,
      {},
    );
  }
}

export const skillGraphService = new SkillGraphService(new FetchClient());
