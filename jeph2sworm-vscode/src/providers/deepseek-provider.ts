/**
 * DeepSeek Provider — proxy to DeepSeek-Coder / DeepSeek-Chat models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class DeepSeekProvider extends BaseProvider {
  readonly name = 'deepseek';
  readonly models = ['deepseek-coder', 'deepseek-chat', 'deepseek-reasoner'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.deepseek.com/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'deepseek-coder';
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
        return 'deepseek-coder';
      case 'planning':
        return 'deepseek-reasoner';
      case 'design':
        return 'deepseek-chat';
      case 'quick':
        return 'deepseek-chat';
    }
  }
}
