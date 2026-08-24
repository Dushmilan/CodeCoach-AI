import { HttpClient } from '@/lib/http-client';
import { FetchClient } from '@/lib/fetch-client';

/** One spaced-repetition card, mirroring the backend ReviewCard. */
export interface ReviewCardItem {
  id: string;
  user_id: string;
  question_id: string;
  error_signature: string;
  state: 'active' | 'scheduled';
  ease: number;
  interval_days: number;
  repetitions: number;
  lapses: number;
  due_at: string;
  last_reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewsDueResponse {
  cards: ReviewCardItem[];
  total: number;
}

/**
 * Client for mistake-memory spaced repetition (Ideas #1). Due cards resurface
 * the learner's own past bugs; grading applies the SM-2 schedule server-side.
 */
export class ReviewService {
  constructor(private http: HttpClient) {}

  async getDue(limit: number = 20): Promise<ReviewsDueResponse> {
    return this.http.get<ReviewsDueResponse>(`/api/reviews/due?limit=${limit}`, {
      cache: 'no-store',
    });
  }

  async grade(cardId: string, quality: number): Promise<ReviewCardItem> {
    const response = await this.http.post<{ card: ReviewCardItem }>(
      `/api/reviews/${encodeURIComponent(cardId)}/grade`,
      { quality },
    );
    return response.card;
  }
}

export const reviewService = new ReviewService(new FetchClient());
