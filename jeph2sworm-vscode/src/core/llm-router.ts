/**
 * LLM Router Client — proxy to set/get LLM provider config on the server.
 */

import { LLMConfig, LLMStats, LLMProvider } from '../types/llm.types';

export class LLMRouterClient {
  constructor(private baseUrl: string) {}

  private async request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) {
      throw new Error(`LLM request failed: ${resp.status}`);
    }
    return resp.json() as Promise<T>;
  }

  async getConfig(): Promise<LLMConfig> {
    return this.request<LLMConfig>('/llm/config');
  }

  async setProvider(provider: LLMProvider, model?: string): Promise<void> {
    await this.request('/llm/provider', 'POST', { provider, model });
  }

  async getStats(): Promise<LLMStats> {
    return this.request<LLMStats>('/llm/stats');
  }

  async getAvailableProviders(): Promise<LLMProvider[]> {
    return this.request<LLMProvider[]>('/llm/providers');
  }

  async getAvailableModels(provider: LLMProvider): Promise<string[]> {
    return this.request<string[]>(`/llm/models/${provider}`);
  }
}
