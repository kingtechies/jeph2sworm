"""xAI / Grok Provider - Grok-2, Grok-2-mini."""

from __future__ import annotations

from typing import List

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = ["grok-2", "grok-2-mini", "grok-2-latest"]

TASK_BEST = {
    "coding": "grok-2",
    "planning": "grok-2",
    "reasoning": "grok-2",
    "design": "grok-2",
    "testing": "grok-2-mini",
    "general": "grok-2",
}


class GrokProvider(BaseProvider):
    provider_name = "xai"
    supports_function_calling = True
    supports_vision = False
    max_context_window = 131_072

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "grok-2")

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
            model=f"xai/{model}" if not model.startswith("xai/") else model,
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
