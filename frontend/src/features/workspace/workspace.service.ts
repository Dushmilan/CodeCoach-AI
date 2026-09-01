import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";

export interface WorkspaceCode {
  code: string;
  language: string;
  updated_at: string | null;
  question_id: string;
}

export interface LastVisited {
  question_id: string;
  language: string | null;
  visited_at: string;
}

export interface ChatMessagePersisted {
  role: "user" | "assistant";
  content: string;
  structured?: unknown;
  timestamp: string;
}

export class WorkspaceService {
  constructor(private http: HttpClient) {}

  async getCode(questionId: string, language: string): Promise<WorkspaceCode> {
    const qs = new URLSearchParams({ language }).toString();
    return this.http.get<WorkspaceCode>(`/api/workspace/code/${encodeURIComponent(questionId)}?${qs}`);
  }

  async saveCode(questionId: string, language: string, code: string): Promise<void> {
    await this.http.put<void>(`/api/workspace/code/${encodeURIComponent(questionId)}`, {
      language,
      code,
    });
  }

  async deleteCode(questionId: string, language: string): Promise<void> {
    const qs = new URLSearchParams({ language }).toString();
    await this.http.delete<void>(`/api/workspace/code/${encodeURIComponent(questionId)}?${qs}`);
  }

  async getLastVisited(): Promise<LastVisited | null> {
    return this.http.get<LastVisited | null>(`/api/workspace/last-visited`);
  }

  async getChat(questionId: string): Promise<{ question_id: string; messages: ChatMessagePersisted[] }> {
    return this.http.get<{ question_id: string; messages: ChatMessagePersisted[] }>(`/api/workspace/chat/${encodeURIComponent(questionId)}`);
  }

  async clearChat(questionId: string): Promise<void> {
    await this.http.delete<void>(`/api/workspace/chat/${encodeURIComponent(questionId)}`);
  }
}

export const workspaceService = new WorkspaceService(new FetchClient());
