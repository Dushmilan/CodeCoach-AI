import { FetchClient } from "./fetch-client";

const client = new FetchClient();

export const apiClient = {
  async get<T>(path: string): Promise<{ data: T }> {
    const data = await client.get<T>(path);
    return { data };
  },
};
