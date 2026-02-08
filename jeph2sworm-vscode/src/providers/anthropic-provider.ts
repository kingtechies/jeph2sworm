/**
 * Anthropic Provider — proxy to Claude 4 / Claude 3.5 Sonnet / Haiku models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class AnthropicProvider extends BaseProvider {
  readonly name = 'anthropic';
  readonly models = ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.anthropic.com/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'claude-sonnet-4-20250514';
    const system = messages.find((m) => m.role === 'system')?.content;
    const filtered = messages.filter((m) => m.role !== 'system');

    const res = await fetch(`${this.config.baseUrl}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.config.apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: chosen,
        max_tokens: 8192,
        system,
        messages: filtered,
      }),
    });
    const data = await res.json();
    return {
      content: data.content?.[0]?.text ?? '',
      model: chosen,
      tokensUsed: (data.usage?.input_tokens ?? 0) + (data.usage?.output_tokens ?? 0),
      finishReason: data.stop_reason ?? 'unknown',
    };
  }

  bestModelFor(task: 'coding' | 'planning' | 'design' | 'quick'): string {
    switch (task) {
      case 'coding':
        return 'claude-sonnet-4-20250514';
      case 'planning':
        return 'claude-sonnet-4-20250514';
      case 'design':
        return 'claude-3-5-sonnet-20241022';
      case 'quick':
        return 'claude-3-5-haiku-20241022';
    }
  }
}
