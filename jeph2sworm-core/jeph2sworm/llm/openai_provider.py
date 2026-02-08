"""OpenAI Provider - GPT-4o, o1, o3 models."""

from __future__ import annotations

from typing import List, Optional

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "o1",
    "o1-mini",
    "o1-preview",
    "o3-mini",
]

TASK_BEST = {
    "coding": "gpt-4o",
    "planning": "o1",
    "reasoning": "o1",
    "design": "gpt-4o",
    "testing": "gpt-4o-mini",
    "general": "gpt-4o",
}


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    supports_function_calling = True
    supports_vision = True
    max_context_window = 128_000

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "gpt-4o")

    async def complete(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        import litellm

        response = await litellm.acompletion(
            model=f"openai/{model}" if not model.startswith("openai/") else model,
            messages=[m.model_dump() for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            **kwargs,
        )

        choice = response.choices[0]
        usage = dict(response.usage) if response.usage else {}

        return LLMResponse(
            content=choice.message.content or "",
            model=model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
        )
