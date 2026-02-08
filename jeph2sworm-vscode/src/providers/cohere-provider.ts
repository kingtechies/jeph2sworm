/**
 * Cohere Provider — proxy to Cohere Command-R / Command-R+ models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class CohereProvider extends BaseProvider {
  readonly name = 'cohere';
  readonly models = ['command-r-plus', 'command-r', 'command-light'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://api.cohere.ai/v2', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'command-r-plus';
    const res = await fetch(`${this.config.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify({ model: chosen, messages }),
    });
    const data = await res.json() as any;
    return {
      content: data.message?.content?.[0]?.text ?? '',
      model: chosen,
      tokensUsed:
        (data.usage?.tokens?.input_tokens ?? 0) + (data.usage?.tokens?.output_tokens ?? 0),
      finishReason: data.finish_reason ?? 'unknown',
    };
  }

  bestModelFor(task: 'coding' | 'planning' | 'design' | 'quick'): string {
    switch (task) {
      case 'coding':
        return 'command-r-plus';
      case 'planning':
        return 'command-r-plus';
      case 'design':
        return 'command-r';
      case 'quick':
        return 'command-light';
    }
  }
}
