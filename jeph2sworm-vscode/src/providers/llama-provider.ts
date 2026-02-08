/**
 * LLaMA Provider — proxy to Meta LLaMA models via local Ollama or compatible API.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class LlamaProvider extends BaseProvider {
  readonly name = 'llama';
  readonly models = ['llama-3.3-70b', 'llama-3.1-8b', 'codellama-70b'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: config.baseUrl ?? 'http://localhost:11434/v1', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'llama-3.3-70b';
    const res = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey ? { Authorization: `Bearer ${this.config.apiKey}` } : {}),
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
        return 'codellama-70b';
      case 'planning':
        return 'llama-3.3-70b';
      case 'design':
        return 'llama-3.3-70b';
      case 'quick':
        return 'llama-3.1-8b';
    }
  }
}
