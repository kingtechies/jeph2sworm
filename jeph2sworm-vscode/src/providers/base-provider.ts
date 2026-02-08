/**
 * Base LLM Provider — abstract interface for all client-side LLM provider proxies.
 */

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMResponse {
  content: string;
  model: string;
  tokensUsed: number;
  finishReason: string;
}

export interface ProviderConfig {
  apiKey: string;
  baseUrl?: string;
  defaultModel?: string;
}

export abstract class BaseProvider {
  abstract readonly name: string;
  abstract readonly models: string[];

  protected config: ProviderConfig;

  constructor(config: ProviderConfig) {
    this.config = config;
  }

  abstract complete(messages: LLMMessage[], model?: string): Promise<LLMResponse>;

  abstract bestModelFor(task: 'coding' | 'planning' | 'design' | 'quick'): string;

  async isAvailable(): Promise<boolean> {
    try {
      await this.complete([{ role: 'user', content: 'ping' }], this.models[this.models.length - 1]);
      return true;
    } catch {
      return false;
    }
  }
}
