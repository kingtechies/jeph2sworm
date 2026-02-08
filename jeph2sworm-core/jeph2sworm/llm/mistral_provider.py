"""Mistral Provider - Mistral Large, Codestral, Mistral Small."""

from __future__ import annotations

from typing import List

import structlog

from jeph2sworm.llm.base_provider import BaseProvider, LLMMessage, LLMResponse

logger = structlog.get_logger()

MODELS = [
    "mistral-large-latest",
    "codestral-latest",
    "mistral-small-latest",
    "mistral-medium-latest",
]

TASK_BEST = {
    "coding": "codestral-latest",
    "planning": "mistral-large-latest",
    "reasoning": "mistral-large-latest",
    "design": "mistral-large-latest",
    "testing": "mistral-small-latest",
    "general": "mistral-large-latest",
}


class MistralProvider(BaseProvider):
    provider_name = "mistral"
    supports_function_calling = True
    supports_vision = False
    max_context_window = 128_000

    def available_models(self) -> List[str]:
        return MODELS

    def best_model_for(self, task: str) -> str:
        return TASK_BEST.get(task, "mistral-large-latest")

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
            model=f"mistral/{model}" if not model.startswith("mistral/") else model,
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
