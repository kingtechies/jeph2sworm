/**
 * Grok Provider — proxy to xAI Grok-2 / Grok-3 models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class GrokProvider extends BaseProvider {
  readonly name = 'grok';
  readonly models = ['grok-3', 'grok-2', 'grok-2-mini'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.x.ai/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'grok-3';
    const res = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({ model: chosen, messages }),
    });
    const data = await res.json();
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
        return 'grok-3';
      case 'planning':
        return 'grok-3';
      case 'design':
        return 'grok-2';
      case 'quick':
        return 'grok-2-mini';
    }
  }
}
