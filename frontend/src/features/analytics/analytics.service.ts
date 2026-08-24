import { apiClient } from "@/lib/api-client";

export type AnalyticsSignal = {
  type: "plateau";
  skill: string;
  title: string;
  detail: string;
  evidence: { failures: number; passes: number; window_days: number; question_ids: string[]; signatures: string[] };
  severity: "warning" | "info";
  first_seen_at: string;
  last_seen_at: string;
};

export type AnalyticsSignalsResponse = { signals: AnalyticsSignal[]; total: number };

export const AnalyticsService = {
  async getSignals(): Promise<AnalyticsSignalsResponse> {
    const res = await apiClient.get<AnalyticsSignalsResponse>("/api/analytics/signals");
    return res.data;
  },
};
