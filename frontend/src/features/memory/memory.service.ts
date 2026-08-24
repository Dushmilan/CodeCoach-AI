import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";

export interface TopicMemoryItem {
  topic: string;
  totalCards: number;
  dueCount: number;
  avgIntervalDays: number;
  daysSinceLastTouch: number | null;
  lapseCount: number;
  energyCostMinutes: number;
  cardIds: string[];
}

export interface MemoryGraphResponse {
  topics: TopicMemoryItem[];
  totalDue: number;
  totalCards: number;
  oldestDueDays?: number | null;
}

/**
 * Client for the forgetting-curve memory graph (Idea #3).
 * Powers the student dashboard: "what am I about to forget?".
 */
export class MemoryService {
  constructor(private http: HttpClient) {}

  async getGraph(): Promise<MemoryGraphResponse> {
    return this.http.get<MemoryGraphResponse>("/api/memory/graph", {
      cache: "no-store",
    });
  }
}

export const memoryService = new MemoryService(new FetchClient());
