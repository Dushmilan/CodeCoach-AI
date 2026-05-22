import { HttpClient } from '@/lib/http-client';
import { FetchClient } from '@/lib/fetch-client';
import { StructuredCoachingResponse } from '@/types';

export interface CoachingRequest {
  problem: string;
  code: string;
  message: string;
  mode: string;
  language: string;
  difficulty?: string;
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
    difficulty: string = 'medium'
  ): Promise<CoachingResponse> {
    const data = await this.http.post<{ response: string; structured: StructuredCoachingResponse | null }>(
      '/api/coach/',
      {
        problem,
        code,
        message,
        mode: mode.toLowerCase(),
        language: language.toLowerCase(),
        difficulty,
      }
    );

    return {
      response: data.response,
      structured: data.structured || null,
    };
  }
}

export const coachingService = new CoachingService(new FetchClient());
