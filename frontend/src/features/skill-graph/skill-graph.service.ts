import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { RecommendedQuestion, SkillGraphResponse } from "@/types";

export class SkillGraphService {
  constructor(private http: HttpClient) {}

  async getGraph(includeBoilerplate: boolean = true): Promise<SkillGraphResponse> {
    const suffix = includeBoilerplate ? "?include_boilerplate=true" : "";
    return this.http.get<SkillGraphResponse>(`/api/skills/me/skills${suffix}`, {
      cache: "no-store",
    });
  }

  async getBoilerplate(): Promise<SkillGraphResponse> {
    return this.http.get<SkillGraphResponse>("/api/skills/boilerplate", {
      cache: "no-store",
    });
  }

  async getRecommendedQuestions(limit: number = 5): Promise<RecommendedQuestion[]> {
    return this.http.get<RecommendedQuestion[]>(
      `/api/skills/me/recommended-questions?limit=${limit}`,
      {
        cache: "no-store",
      },
    );
  }

  async syncFromSubmissions(): Promise<{ accepted: number; duplicate: number; invalid: number; skipped: number }> {
    return this.http.post<{ accepted: number; duplicate: number; invalid: number; skipped: number }>(
      `/api/skills/me/sync`,
      {},
    );
  }
}

export const skillGraphService = new SkillGraphService(new FetchClient());
