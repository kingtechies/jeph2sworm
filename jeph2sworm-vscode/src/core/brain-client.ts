/**
 * Brain Client — REST/WS interface to the Brain module on the server.
 */

import * as vscode from 'vscode';
import { BrainStats, BrainDecision, BrainContext } from '../types/brain.types';

export class BrainClient {
  constructor(private baseUrl: string) {}

  private async request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) {
      throw new Error(`Brain request failed: ${resp.status} ${resp.statusText}`);
    }
    return resp.json() as Promise<T>;
  }

  async getStats(): Promise<BrainStats> {
    return this.request<BrainStats>('/brain/stats');
  }

  async getContext(agent: string): Promise<BrainContext> {
    return this.request<BrainContext>(`/brain/context/${agent}`);
  }

  async getDecisions(): Promise<BrainDecision[]> {
    return this.request<BrainDecision[]>('/brain/decisions');
  }

  async getSection(section: string): Promise<unknown> {
    return this.request(`/brain/${section}`);
  }

  async updateSection(section: string, data: unknown): Promise<void> {
    await this.request(`/brain/${section}`, 'PUT', data);
  }

  async search(query: string): Promise<unknown[]> {
    return this.request<unknown[]>(`/brain/search?q=${encodeURIComponent(query)}`);
  }

  async getProjectSpec(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('/brain/project_spec');
  }

  async getTaskBoard(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('/brain/task_board');
  }
}
