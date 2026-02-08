"""Anthropic Provider - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku."""

from __future__ import annotations

from typing import List, Optional

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
]

TASK_BEST = {
    "coding": "claude-sonnet-4-20250514",
    "planning": "claude-3-opus-20240229",
    "reasoning": "claude-3-opus-20240229",
    "design": "claude-sonnet-4-20250514",
    "testing": "claude-3-haiku-20240307",
    "general": "claude-sonnet-4-20250514",
}


class AnthropicProvider(BaseProvider):
    provider_name = "anthropic"
    supports_function_calling = True
    supports_vision = True
    max_context_window = 200_000

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "claude-sonnet-4-20250514")

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
            model=f"anthropic/{model}" if not model.startswith("anthropic/") else model,
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
