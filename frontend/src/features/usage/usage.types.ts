export interface UsageInfo {
  plan: string;
  daily_limit: number;
  daily_used: number;
  daily_remaining: number;
  reset_at: string;
}
