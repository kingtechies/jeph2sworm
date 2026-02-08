"""Cohere Provider - Command R+, Command R."""

from __future__ import annotations

from typing import List

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "command-r-plus",
    "command-r",
    "command-light",
]

TASK_BEST = {
    "coding": "command-r-plus",
    "planning": "command-r-plus",
    "reasoning": "command-r-plus",
    "design": "command-r",
    "testing": "command-light",
    "general": "command-r",
}


class CohereProvider(BaseProvider):
    provider_name = "cohere"
    supports_function_calling = True
    supports_vision = False
    max_context_window = 128_000

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "command-r")

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
            model=f"cohere/{model}" if not model.startswith("cohere/") else model,
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
