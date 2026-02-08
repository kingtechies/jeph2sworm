/**
 * LLM types for the VS Code extension.
 */

export type LLMProvider =
  | 'openai'
  | 'anthropic'
  | 'xai'
  | 'gemini'
  | 'deepseek'
  | 'mistral'
  | 'together_ai'
  | 'cohere';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  apiKey?: string;
}

export interface TokenUsage {
  agent: string;
  provider: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCostUsd: number;
}

export interface LLMStats {
  totalRequests: number;
  totalTokens: number;
  estimatedCostUsd: number;
  byAgent: Record<string, number>;
  byProvider: Record<string, number>;
}
