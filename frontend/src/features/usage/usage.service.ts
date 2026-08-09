import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import { UsageInfo } from "./usage.types";

export class UsageService {
  constructor(private http: HttpClient) {}

  async getUsage(): Promise<UsageInfo> {
    return this.http.get<UsageInfo>("/api/usage");
  }
}

export const usageService = new UsageService(new FetchClient());
