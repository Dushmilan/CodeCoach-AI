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
  lesson_context?: string;
}

export interface CoachingResponse {
  response: string;
  structured: StructuredCoachingResponse | null;
}

export class CoachingService {
  constructor(private http: HttpClient) {}

  private getApiKeyHeader(): Record<string, string> {
    if (typeof window === 'undefined') return {};
    const key = localStorage.getItem('nvidia_api_key');
    return key ? { 'X-NVIDIA-API-Key': key } : {};
  }

  async getCoachResponse(
    problem: string,
    language: string,
    code: string,
    message: string,
    mode: string,
    difficulty: string = 'medium',
    lessonContext?: string
  ): Promise<CoachingResponse> {
    const headers = this.getApiKeyHeader();
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
    const data = await this.http.post<{ response: string; structured: StructuredCoachingResponse | null }>(
      '/api/coach/',
      body,
      { headers }
    );

    return {
      response: data.response,
      structured: data.structured || null,
    };
  }
}

export const coachingService = new CoachingService(new FetchClient());
