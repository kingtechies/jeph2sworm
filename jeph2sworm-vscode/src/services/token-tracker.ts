/**
 * Token Tracker - Client-side LLM usage tracking for status bar display.
 */

import * as vscode from 'vscode';
import { LLMStats } from '../types/llm.types';
import { WebSocketService } from './websocket-service';

export class TokenTrackerService {
  private statusBarItem: vscode.StatusBarItem;
  private stats: LLMStats = {
    totalRequests: 0,
    totalTokens: 0,
    estimatedCostUsd: 0,
    byAgent: {},
    byProvider: {},
  };

  constructor(ws: WebSocketService) {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      90
    );
    this.statusBarItem.command = 'jeph2sworm.showTokenUsage';
    this.updateDisplay();
    this.statusBarItem.show();

    // Listen for token usage events
    ws.on('*', (event) => {
      if (event.data?.usage) {
        this.recordUsage(event.data.usage as any);
      }
    });
  }

  recordUsage(usage: {
    agent: string;
    provider: string;
    promptTokens: number;
    completionTokens: number;
  }): void {
    this.stats.totalRequests++;
    this.stats.totalTokens += (usage.promptTokens || 0) + (usage.completionTokens || 0);
    this.stats.byAgent[usage.agent] = (this.stats.byAgent[usage.agent] || 0) + usage.promptTokens + usage.completionTokens;
    this.stats.byProvider[usage.provider] = (this.stats.byProvider[usage.provider] || 0) + usage.promptTokens + usage.completionTokens;

    // Rough cost estimate
    this.stats.estimatedCostUsd = this.stats.totalTokens * 0.000003; // ~$3/1M tokens average

    this.updateDisplay();
  }

  getStats(): LLMStats {
    return { ...this.stats };
  }

  private updateDisplay(): void {
    const tokens = this.formatTokens(this.stats.totalTokens);
    const cost = this.stats.estimatedCostUsd.toFixed(2);
    this.statusBarItem.text = `$(symbol-number) ${tokens} tokens (~$${cost})`;
    this.statusBarItem.tooltip = `jeph2sworm LLM Usage\n${this.stats.totalRequests} requests\n${this.stats.totalTokens} tokens\n~$${cost} estimated cost`;
  }

  private formatTokens(n: number): string {
    if (n >= 1_000_000) { return (n / 1_000_000).toFixed(1) + 'M'; }
    if (n >= 1_000) { return (n / 1_000).toFixed(1) + 'K'; }
    return n.toString();
  }

  dispose(): void {
    this.statusBarItem.dispose();
  }
}
