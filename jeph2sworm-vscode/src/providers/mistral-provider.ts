/**
 * Mistral Provider — proxy to Mistral Large / Medium / Small models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class MistralProvider extends BaseProvider {
  readonly name = 'mistral';
  readonly models = ['mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest', 'codestral-latest'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.mistral.ai/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'mistral-large-latest';
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
        return 'codestral-latest';
      case 'planning':
        return 'mistral-large-latest';
      case 'design':
        return 'mistral-medium-latest';
      case 'quick':
        return 'mistral-small-latest';
    }
  }
}
