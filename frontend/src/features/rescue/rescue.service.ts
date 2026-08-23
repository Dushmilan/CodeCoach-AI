import { HttpClient } from '@/lib/http-client';
import { FetchClient } from '@/lib/fetch-client';

/** One durable re-surface queue row, mirroring the backend RescueItem. */
export interface RescueQueueItem {
  id: string;
  user_id: string;
  question_id: string;
  status: 'abandoned' | 'completed' | 'dismissed';
  first_abandoned_at: string;
  due_at: string;
  resurface_count: number;
  last_intervention_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RescueDueResponse {
  items: RescueQueueItem[];
  total: number;
}

/**
 * Client for the durable rescue re-surface queue (the "never-alone"
 * contract's persistence half). Abandoned problems resurface tomorrow
 * morning as tiny re-entry steps.
 */
export class RescueService {
  constructor(private http: HttpClient) {}

  async getDue(limit: number = 50): Promise<RescueDueResponse> {
    return this.http.get<RescueDueResponse>(`/api/rescue/due?limit=${limit}`, {
      cache: 'no-store',
    });
  }

  /** Record an abandonment. Resolves to null when the question was dismissed. */
  async abandon(
    questionId: string,
    tzOffsetMinutesEast?: number,
  ): Promise<RescueQueueItem | null> {
    const body =
      tzOffsetMinutesEast === undefined
        ? undefined
        : { tz_offset_minutes: tzOffsetMinutesEast };
    const response = await this.http.post<{
      item: RescueQueueItem | null;
    }>(`/api/rescue/${encodeURIComponent(questionId)}/abandon`, body);
    return response.item;
  }

  async complete(questionId: string): Promise<RescueQueueItem | null> {
    const response = await this.http.post<{
      item: RescueQueueItem | null;
    }>(`/api/rescue/${encodeURIComponent(questionId)}/complete`);
    return response.item;
  }

  async dismiss(questionId: string): Promise<RescueQueueItem | null> {
    const response = await this.http.post<{
      item: RescueQueueItem | null;
    }>(`/api/rescue/${encodeURIComponent(questionId)}/dismiss`);
    return response.item;
  }
}

export const rescueService = new RescueService(new FetchClient());
