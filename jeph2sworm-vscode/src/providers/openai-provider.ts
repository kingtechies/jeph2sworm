/**
 * OpenAI Provider — proxy to GPT-4o / GPT-4-turbo / o1 models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class OpenAIProvider extends BaseProvider {
  readonly name = 'openai';
  readonly models = ['gpt-4o', 'gpt-4-turbo', 'gpt-4o-mini', 'o1', 'o1-mini'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.openai.com/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'gpt-4o';
    const res = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({ model: chosen, messages }),
    });
    const data = await res.json() as any;
    return {
      content: data.choices?.[0]?.message?.content ?? '',
      model: chosen,
      tokensUsed: data.usage?.total_tokens ?? 0,
      finishReason: data.choices?.[0]?.finish_reason ?? 'unknown',
    };
  }

  bestModelFor(task: 'coding' | 'planning' | 'design' | 'quick'): string {
    switch (task) {
      case 'coding':
        return 'gpt-4o';
      case 'planning':
        return 'o1';
      case 'design':
        return 'gpt-4o';
      case 'quick':
        return 'gpt-4o-mini';
    }
  }
}
