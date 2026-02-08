/**
 * Gemini Provider — proxy to Google Gemini Pro / Ultra / Flash models.
 */

import { BaseProvider, LLMMessage, LLMResponse, ProviderConfig } from './base-provider';

export class GeminiProvider extends BaseProvider {
  readonly name = 'gemini';
  readonly models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash'];

  constructor(config: ProviderConfig) {
    super({ baseUrl: 'https://generativelanguage.googleapis.com/v1beta', ...config });
  }

  async complete(messages: LLMMessage[], model?: string): Promise<LLMResponse> {
    const chosen = model ?? this.config.defaultModel ?? 'gemini-2.5-pro';
    const contents = messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
      }));
    const systemInstruction = messages.find((m) => m.role === 'system');

    const res = await fetch(
      `${this.config.baseUrl}/models/${chosen}:generateContent?key=${this.config.apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents,
          ...(systemInstruction
            ? { systemInstruction: { parts: [{ text: systemInstruction.content }] } }
            : {}),
        }),
      }
    );
    const data = await res.json() as any;
    const candidate = data.candidates?.[0];
    return {
      content: candidate?.content?.parts?.[0]?.text ?? '',
      model: chosen,
      tokensUsed:
        (data.usageMetadata?.promptTokenCount ?? 0) +
        (data.usageMetadata?.candidatesTokenCount ?? 0),
      finishReason: candidate?.finishReason ?? 'unknown',
    };
  }

  bestModelFor(task: 'coding' | 'planning' | 'design' | 'quick'): string {
    switch (task) {
      case 'coding':
        return 'gemini-2.5-pro';
      case 'planning':
        return 'gemini-2.5-pro';
      case 'design':
        return 'gemini-2.5-flash';
      case 'quick':
        return 'gemini-2.0-flash';
    }
  }
}
